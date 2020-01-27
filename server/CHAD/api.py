import ipaddress

from marshmallow import Schema, fields
from marshmallow.validate import Range
from flask import current_app as app, jsonify

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

@app.route('/ovpn/<user_id>')
def ovpn_get(user_id):
    return app.pki.generate_client_ovpn(user_id)

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
