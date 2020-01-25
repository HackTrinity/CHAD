from gevent import monkey; monkey.patch_all()

import os

import docker
import redis
from werkzeug.exceptions import InternalServerError
from marshmallow.exceptions import ValidationError
from flask import Flask, jsonify

from .util import var_or_secret
from . import stack, challenges, cleanup

app = Flask(__name__)
app.config.update({
    'DOCKER_REGISTRY': os.getenv('DOCKER_REGISTRY', 'example.com'),
    'ID_SALT': var_or_secret('ID_SALT', 'TESTTESTTEST'),
    'FLAG_PREFIX': os.getenv('FLAG_PREFIX', 'CTF'),
    'REDIS_URL': os.getenv('REDIS_URL', 'redis://redis'),
    'GATEWAY_IMAGE': os.getenv('GATEWAY_IMAGE', 'chad-gateway'),
    'GATEWAY_PROXY': os.getenv('GATEWAY_PROXY', 'chad-gw.sys.hacktrinity.org'),
    'CHALLENGE_DOMAIN': os.getenv('CHALLENGE_DOMAIN', 'challs.hacktrinity.org'),
    'TRAEFIK_NETWORK': os.getenv('TRAEFIK_NETWORK', 'traefik'),
    'CLEANUP_INTERVAL': int(os.getenv('CLEANUP_INTERVAL', '30')),
    'CLEANUP_TIMEOUT': int(os.getenv('CLEANUP_TIMEOUT', '60'))
})

app.redis = redis.from_url(app.config['REDIS_URL'])
app.challenges = challenges.ChallengeManager(
    docker.from_env(),
    stack.StackManager(),
    app.redis,
    app.config['ID_SALT'],
    docker_registry=app.config['DOCKER_REGISTRY'],
    flag_prefix=app.config['FLAG_PREFIX'],
    timeout=app.config['CLEANUP_TIMEOUT'],
    gateway_image=app.config['GATEWAY_IMAGE'],
    gateway_proxy=app.config['GATEWAY_PROXY'],
    challenge_domain=app.config['CHALLENGE_DOMAIN'],
    traefik_network=app.config['TRAEFIK_NETWORK']
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
