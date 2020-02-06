import os

from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.plugins import register_plugin_assets_directory, override_template

from . import models, api

def load(app):
    app.db.create_all()

    CHALLENGE_CLASSES["chad"] = models.CHADChallenge

    register_plugin_assets_directory(
        app, base_path="/plugins/STACY/assets/"
    )

    app.register_blueprint(api.blueprint)

    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'assets', 'challenges.html')) as template:
        override_template('challenges.html', template.read())
