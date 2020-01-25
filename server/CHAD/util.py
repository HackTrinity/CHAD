from functools import wraps
import itertools
import random
import os

from marshmallow import Schema
from flask import request, jsonify

def nth(iterable, n, default=None):
    "Returns the nth item or a default value"
    return next(itertools.islice(iterable, n, None), default)

def var_or_secret(var, default=None, default_file=None, binary=False):
    value = os.getenv(var)
    if not value:
        try:
            secret_file = os.getenv(f'{var}_FILE', default_file)
            if secret_file:
                with open(secret_file, 'rb' if binary else 'r') as secret:
                    value = secret.read()
                    if not binary:
                        value = value.strip()
            else:
                value = default
        except (OSError, IOError):
            value = default
    return value

# An XKCD 936-compliant (https://xkcd.com/936/) flag generator
class FlagGenerator:
    def __init__(self, prefix='CTF', words=4):
        self.prefix = prefix
        self.wcount = words

        self.random = random.Random()
        with open('CHAD/nouns.txt') as wordlist:
            self.words = [w.strip() for w in wordlist]

    def next_flag(self):
        return f'{self.prefix}{{{"_".join(map(lambda _: self.random.choice(self.words), range(self.wcount)))}}}'

def parse_body(schema: Schema):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({'message': 'json request body required'}), 400

            return fn(schema.load(data), *args, **kwargs)
        return wrapper
    return decorator
