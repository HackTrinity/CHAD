import ipaddress

from marshmallow import Schema, fields
from marshmallow.validate import Range
from flask import current_app as app, jsonify

from . import challenges
from .util import parse_body

def validate_network(n):
    try:
        ipaddress.IPv4Network(n)
        return True
    except ValueError:
        return False

class CreateInstanceSchema(Schema):
    challenge_id = fields.Int(required=True, strict=True, validate=Range(min=1))
    user_id = fields.Int(required=True, strict=True, validate=Range(min=1))
    stack = fields.Dict(required=True)
    service = fields.Str(required=True)
    needs_flag = fields.Bool(missing=True)
create_schema = CreateInstanceSchema()


@app.route('/gateways/<user_id>', methods=['POST'])
def gateway_create(user_id):
    app.challenges.ensure_gateway_up(user_id)
    return '', 204

@app.route('/gateways/<user_id>', methods=['DELETE'])
def gateway_delete(user_id):
    app.challenges.ensure_gateway_gone(user_id)
    return '', 204

@app.route('/gateways/<user_id>/ovpn/client')
def ovpn_client_get(user_id):
    return app.pki.generate_client_ovpn(user_id)

if app.debug:
    @app.route('/gateways/<user_id>/ovpn/server')
    def ovpn_server_get(user_id):
        return app.pki.generate_server_ovpn(user_id, challenges.POOL_START, challenges.POOL_END, challenges.NETWORK)


@app.route('/instances', methods=['POST'])
@parse_body(create_schema)
def instance_create(b):
    return jsonify(app.challenges.create(
        b['challenge_id'],
        b['user_id'],
        b['stack'],
        b['service'],
        b['needs_flag']
    ))

@app.route('/instances/<challenge_id>/<user_id>', methods=['PATCH'])
def instance_ping(challenge_id, user_id):
    app.challenges.ping(int(challenge_id), int(user_id))
    return '', 204

@app.route('/instances/<challenge_id>/<user_id>', methods=['PUT'])
def instance_reset(challenge_id, user_id):
    app.challenges.reset(int(challenge_id), int(user_id))
    return '', 204

@app.route('/instances/<challenge_id>/<user_id>', methods=['DELETE'])
def instance_delete(challenge_id, user_id):
    app.challenges.delete(int(challenge_id), int(user_id))
    return '', 204
