import os

import yaml
from flask import Blueprint, Response, current_app as app, abort
from flask_restplus import Api, Resource

from CTFd.utils.config import ctf_name
from CTFd.utils.user import get_current_user, is_admin
from CTFd.utils.decorators import authed_only

from . import backend
from .models import GeneratedFlags, CHADChallengeModel

app.config["CHAD_ENDPOINT"] = os.getenv("CHAD_ENDPOINT", "http://chad")
chad = backend.CHADClient(app.config["CHAD_ENDPOINT"])

blueprint = Blueprint("stacy", __name__, url_prefix="/plugins/stacy")
api = Api(blueprint, prefix="/api", doc=app.config.get("SWAGGER_UI"))

@blueprint.route("/ovpn")
@authed_only
def get_ovpn():
    user = get_current_user()
    res = Response(chad.get_ovpn(user.id), mimetype="application/x-openvpn-profile")
    res.headers["Content-Disposition"] = f"attachment; filename={ctf_name()}_{user.name}.ovpn"
    return res

@api.route('/instances/<int:chall_id>')
class InstanceManagement(Resource):
    @authed_only
    def post(self, chall_id):
        user = get_current_user()
        challenge = CHADChallengeModel.query.filter_by(id=chall_id).first_or_404()

        if challenge.state == "hidden" and not is_admin():
            abort(403)

        try:
            flag, should_store = GeneratedFlags.get_instance_arg(user, challenge)
        except KeyError:
            return {"success": False, "errors": ["No static flags have been configured"]}, 500

        stack = yaml.safe_load(challenge.stack)
        info = chad.create_instance(user.id, challenge.id, stack, challenge.service, flag)
        if should_store:
            GeneratedFlags.create(user, challenge, info['flag'])

        return {"success": True}

    def delete(self, chall_id):
        user = get_current_user()
        challenge = CHADChallengeModel.query.filter_by(id=chall_id).first_or_404()

        chad.delete_instance(user.id, challenge.id)
        return {"success": True}
