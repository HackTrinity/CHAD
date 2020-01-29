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

def subset_sum(numbers, target, required_numbers=-1, partial=[], partial_sum=0):
    if len(partial) == required_numbers and partial_sum == target:
        yield partial
    if partial_sum >= target:
        return
    for i, n in enumerate(numbers):
        remaining = numbers[i + 1:]
        yield from subset_sum(remaining, target, required_numbers, partial + [n], partial_sum + n)

class FlagLengthError(Exception):
    pass

# An XKCD 936-compliant (https://xkcd.com/936/) flag generator
class FlagGenerator:
    def __init__(self, prefix='CTF', words=4, max_length=64):
        self.prefix = prefix
        self.words_per_flag = words
        self.fixed_space = len(self.prefix) + 1 + (self.words_per_flag - 1) + 1

        self.random = random.Random()

        self.words = {}
        with open('CHAD/nouns.txt') as wordlist:
            for word in wordlist:
                word = word.strip()
                l = len(word)
                if l not in self.words:
                    self.words[l] = []
                self.words[l].append(word)

        self.max_length = max_length
        if (max(self.words.keys()) * self.words_per_flag) + self.fixed_space < self.max_length:
            raise FlagLengthError(f'Not enough long words to produce up to {self.max_length} character flags')

        self.length_combinations = {}
        lengths = list(self.words.keys())
        for l in range(min(self.words.keys()), self.max_length + 1):
            combinations = list(subset_sum(lengths, l, self.words_per_flag))
            if combinations:
                self.length_combinations[l] = combinations
        self.min_length = min(self.length_combinations.keys()) + self.fixed_space

    def format_flag(self, flag):
        return f'{self.prefix}{{{flag}}}'
    def next_flag(self, length=None):
        if not length:
            length = self.random.randrange(self.min_length, self.max_length + 1)

        if length < self.min_length or length > self.max_length:
            raise FlagLengthError(f'Impossible to generate a {self.words_per_flag} word flag which is ' +
                f'{length} characters')

        length -= self.fixed_space
        lengths = list(self.random.choice(self.length_combinations[length]))
        self.random.shuffle(lengths)
        return self.format_flag('_'.join(map(lambda l: self.random.choice(self.words[l]), lengths)))

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
