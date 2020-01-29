import os

from flask import Blueprint, Response, current_app as app
from flask_restplus import Api, Resource

from CTFd.utils.config import ctf_name
from CTFd.utils.user import get_current_user
from CTFd.utils.decorators import authed_only

from . import backend

app.config["CHAD_ENDPOINT"] = os.getenv("CHAD_ENDPOINT", "http://chad")
chad = backend.CHADClient(app.config["CHAD_ENDPOINT"])

blueprint = Blueprint("stacy", __name__, url_prefix="/plugins/stacy")
api = Api(blueprint, prefix="/api", doc=app.config.get("SWAGGER_UI"))

@blueprint.route("/ovpn")
@authed_only
def get_ovpn():
    user = get_current_user()
    res = Response(chad.get_ovpn(user.id), mimetype='application/x-openvpn-profile')
    res.headers["Content-Disposition"] = f"attachment; filename={ctf_name()}_{user.name}.ovpn"
    return res
