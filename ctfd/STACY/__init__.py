from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.plugins import register_plugin_assets_directory

from . import models

def load(app):
    app.db.create_all()
    CHALLENGE_CLASSES["chad"] = models.CHADChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/STACY/assets/"
    )
