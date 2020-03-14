# pylint: disable=wrong-import-order,wrong-import-position
from gevent import monkey; monkey.patch_all()

import os

import docker
import redis
from werkzeug.exceptions import InternalServerError
from marshmallow.exceptions import ValidationError
from flask import Flask, jsonify

from .util import var_or_secret
from . import stack, pki, challenges, cleanup

app = Flask(__name__)
app.config.update({
    'DOCKER_REGISTRY': os.getenv('DOCKER_REGISTRY', 'example.com'),
    'ID_SALT': var_or_secret('ID_SALT', 'TESTTESTTEST'),
    'FLAG_PREFIX': os.getenv('FLAG_PREFIX', 'CTF'),
    'REDIS_URL': os.getenv('REDIS_URL', 'redis://redis'),
    'GATEWAY_IMAGE': os.getenv('GATEWAY_IMAGE', 'chad-gateway'),
    'GATEWAY_DOMAIN': os.getenv('GATEWAY_PROXY', 'chad-gw.sys.hacktrinity.org'),
    'TRAEFIK_NETWORK': os.getenv('TRAEFIK_NETWORK', 'traefik'),
    'CLEANUP_INTERVAL': int(os.getenv('CLEANUP_INTERVAL', '30')),
    'CLEANUP_INSTANCE_TIMEOUT': int(os.getenv('CLEANUP_INSTANCE_TIMEOUT', '60')),
    'CLEANUP_GATEWAY_TIMEOUT': int(os.getenv('CLEANUP_GATEWAY_TIMEOUT', '120')),
    'NETWORK_PLUGIN': os.getenv('NETWORK_PLUGIN', 'weaveworks/net-plugin:latest_release')
})

app.redis = redis.from_url(app.config['REDIS_URL'])
app.pki = pki.PKI(domain=app.config['GATEWAY_DOMAIN'])
app.challenges = challenges.ChallengeManager(
    docker.from_env(),
    app.pki,
    stack.StackManager(),
    app.redis,
    app.config['ID_SALT'],
    docker_registry=app.config['DOCKER_REGISTRY'],
    flag_prefix=app.config['FLAG_PREFIX'],
    instance_timeout=app.config['CLEANUP_INSTANCE_TIMEOUT'],
    gateway_timeout=app.config['CLEANUP_GATEWAY_TIMEOUT'],
    gateway_image=app.config['GATEWAY_IMAGE'],
    gateway_domain=app.config['GATEWAY_DOMAIN'],
    traefik_network=app.config['TRAEFIK_NETWORK'],
    network_plugin=app.config['NETWORK_PLUGIN']
)
app.cleanup = cleanup.Cleanup(
    app.challenges,
    interval=app.config['CLEANUP_INTERVAL']
)

with app.app_context():
    from . import api

@app.errorhandler(404)
def not_found(_e):
    return jsonify({'message': 'not found'}), 404

@app.errorhandler(ValidationError)
def validation_error(e):
    return jsonify({'message': 'validation error', 'extra': e.messages}), 400

@app.errorhandler(InternalServerError)
def internal_error(e):
    original = getattr(e, 'original_exception', None)

    if original is None:
        return jsonify({'message': 'unknown error'}), 500
    return jsonify({'message': str(original)}), 500
