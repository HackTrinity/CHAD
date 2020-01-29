import ipaddress

from marshmallow import Schema, fields, post_load, ValidationError
from marshmallow.validate import Range
from flask import current_app as app, jsonify

from . import util, challenges
from .util import parse_body

def validate_network(n):
    try:
        ipaddress.IPv4Network(n)
        return True
    except ValueError:
        return False

class CreateInstanceSchema(Schema):
    user_id = fields.Int(required=True, strict=True, validate=Range(min=1))
    challenge_id = fields.Int(required=True, strict=True, validate=Range(min=1))
    stack = fields.Dict(required=True)
    service = fields.Str(required=True)
    needs_flag = fields.Bool(missing=True)
    flag = fields.Field(required=True)

    @post_load
    def check_flag(self, data, **_kwargs):
        if not isinstance(data['flag'], str) and \
            not isinstance(data['flag'], int) and \
            not isinstance(data['flag'], bool):
            raise ValidationError('"flag" must be a boolean, an integer or a string')
        return data

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
        b['user_id'],
        b['challenge_id'],
        b['stack'],
        b['service'],
        b['flag']
    ))

@app.route('/instances/<user_id>/<challenge_id>', methods=['PATCH'])
def instance_ping(user_id, challenge_id):
    app.challenges.ping(int(user_id), int(challenge_id))
    return '', 204

@app.route('/instances/<user_id>/<challenge_id>', methods=['PUT'])
def instance_reset(user_id, challenge_id):
    app.challenges.reset(int(user_id), int(challenge_id))
    return '', 204

@app.route('/instances/<user_id>/<challenge_id>', methods=['DELETE'])
def instance_delete(user_id, challenge_id):
    app.challenges.delete(int(user_id), int(challenge_id))
    return '', 204


@app.errorhandler(util.FlagLengthError)
def err_flag_length(e):
    return jsonify({'message': str(e)}), 400

@app.errorhandler(challenges.InstanceNotFoundError)
def err_instance_not_found(e):
    return jsonify({'message': str(e)}), 404

@app.errorhandler(challenges.InstanceExistsError)
def err_instance_exists(e):
    return jsonify({'message': str(e)}), 409
