import os

import yaml
from flask import Blueprint, Response, current_app as app, abort
from flask_restplus import Api, Resource

from CTFd.utils.config import ctf_name, is_teams_mode
from CTFd.utils.user import get_current_user, is_admin
from CTFd.utils.decorators import (
    during_ctf_time_only,
    require_verified_emails,
    authed_only,
    require_team,
)
from CTFd.utils.decorators.visibility import check_challenge_visibility

from . import backend
from .models import GeneratedFlags, CHADChallengeModel

app.config["CHAD_ENDPOINT"] = os.getenv("CHAD_ENDPOINT", "http://chad")
chad = backend.CHADClient(app.config["CHAD_ENDPOINT"])

blueprint = Blueprint("stacy", __name__, url_prefix="/plugins/stacy")
api = Api(blueprint, prefix="/api", doc=app.config.get("SWAGGER_UI"))

@blueprint.route("/ovpn")
@authed_only
@require_team
@require_verified_emails
def get_ovpn():
    user = get_current_user()
    if is_teams_mode():
        uid = user.team_id
        name = user.team.name
    else:
        uid = user.id
        name = user.name

    res = Response(chad.get_ovpn(uid), mimetype="application/x-openvpn-profile")
    res.headers["Content-Disposition"] = f"attachment; filename={ctf_name()}_{name}.ovpn"
    return res

@api.route('/instances/<int:chall_id>')
class InstanceManagement(Resource):
    @during_ctf_time_only
    @check_challenge_visibility
    @authed_only
    @require_team
    @require_verified_emails
    def post(self, chall_id):
        user = get_current_user()
        uid = user.team_id if is_teams_mode() else user.id
        challenge = CHADChallengeModel.query.filter_by(id=chall_id).first_or_404()

        if challenge.state == "hidden" and not is_admin():
            abort(403)

        try:
            flag, should_store = GeneratedFlags.get_instance_arg(user, challenge)
        except KeyError:
            return {"success": False, "message": "No static flags have been configured"}, 500

        stack = yaml.safe_load(challenge.stack)
        info = chad.create_instance(uid, challenge.id, stack, challenge.service, flag)
        if should_store:
            GeneratedFlags.create(user, challenge, info['flag'])

        return {"success": True}

    @during_ctf_time_only
    @check_challenge_visibility
    @authed_only
    @require_team
    @require_verified_emails
    def delete(self, chall_id):
        user = get_current_user()
        uid = user.team_id if is_teams_mode() else user.id
        challenge = CHADChallengeModel.query.filter_by(id=chall_id).first_or_404()

        chad.delete_instance(uid, challenge.id)
        return {"success": True}

    @during_ctf_time_only
    @check_challenge_visibility
    @authed_only
    @require_team
    @require_verified_emails
    def put(self, chall_id):
        user = get_current_user()
        uid = user.team_id if is_teams_mode() else user.id
        challenge = CHADChallengeModel.query.filter_by(id=chall_id).first_or_404()

        chad.reset_instance(uid, challenge.id)
        return {"success": True}

    @during_ctf_time_only
    @check_challenge_visibility
    @authed_only
    @require_team
    @require_verified_emails
    def patch(self, chall_id):
        user = get_current_user()
        uid = user.team_id if is_teams_mode() else user.id
        challenge = CHADChallengeModel.query.filter_by(id=chall_id).first_or_404()

        chad.ping_instance(uid, challenge.id)
        return {"success": True}


@api.errorhandler(backend.InstanceNotFoundError)
def err_instance_not_found(e):
    return {"success": False, "message": str(e)}, 404

@api.errorhandler(backend.InstanceExistsError)
def err_instance_exists(e):
    return {"success": False, "message": str(e)}, 409
