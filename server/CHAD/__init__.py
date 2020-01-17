from gevent import monkey; monkey.patch_socket()

import time

from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello, world!'

@app.route('/sleep')
def sleep():
    time.sleep(5)
    return 'slept'
