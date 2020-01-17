from gevent import monkey; monkey.patch_all()

import time

import docker
from flask import Flask, jsonify

from . import stack

app = Flask(__name__)
app.docker = docker.from_env()
app.stacks = stack.StackManager()

@app.route('/')
def index():
    return 'Hello, world!'

@app.route('/stacks')
def stacks():
    return jsonify(app.stacks.list_all())

@app.route('/stacks/<id_>')
def services(id_):
    return jsonify(app.stacks.services(id_))

@app.route('/services/<id_>')
def info(id_):
    return jsonify(app.docker.services.get(id_).attrs)
