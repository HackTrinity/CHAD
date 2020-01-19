from marshmallow import Schema, fields
from marshmallow.validate import Range
from flask import current_app as app, jsonify

from .util import parse_body

class CreateInstanceSchema(Schema):
    challenge_id = fields.Int(required=True, strict=True, validate=Range(min=1))
    user_id = fields.Int(required=True, strict=True, validate=Range(min=1))
    stack = fields.Dict(required=True)
    service = fields.Str(required=True)
    needs_flag = fields.Bool(missing=True)
    needs_gateway = fields.Bool(missing=False)
create_schema = CreateInstanceSchema()

@app.route('/instances', methods=['POST'])
@parse_body(create_schema)
def instance_create(b):
    return jsonify(app.challenges.create(
        b['challenge_id'],
        b['user_id'],
        b['stack'],
        b['service'],
        b['needs_flag'],
        b['needs_gateway']
    ))

@app.route('/instances/<challenge_id>/<user_id>', methods=['PUT'])
def instance_reset(challenge_id, user_id):
    app.challenges.reset(int(challenge_id), int(user_id))
    return '', 204

@app.route('/instances/<challenge_id>/<user_id>', methods=['DELETE'])
def instance_delete(challenge_id, user_id):
    app.challenges.delete(int(challenge_id), int(user_id))
    return '', 204
