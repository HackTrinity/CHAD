from string import Template
import json
import tempfile
import time

import dpath.util as dpath
import hashids

from . import util

LABEL_PREFIX = 'org.hacktrinity.chad'
LABEL_PRIMARY = f'{LABEL_PREFIX}.primary'

def stack_name(c, u):
    return f'chad_{c}_{u}'

class ChallengeException(Exception):
    pass

class ChallengeManager:
    def __init__(self, docker, stacks, redis, salt, flag_prefix='CTF', timeout=60):
        self.ids = hashids.Hashids(salt, min_length=10)
        self.flags = util.FlagGenerator(prefix=flag_prefix)

        self.docker = docker
        self.stacks = stacks
        self.redis = redis
        self.timeout = timeout

    def cleanup(self, logger=None):
        now = int(time.time())
        for stack in filter(lambda s: s.startswith('chad_'), self.stacks.ls()):
            key = f'{stack}_last_ping'
            last = self.redis.get(key)
            if last is None:
                # Give a chance for an untracked instance to be pinged
                self.redis.set(key, now)
                continue

            last = int(last)
            if now - last > self.timeout:
                if logger:
                    logger.info('cleaning up defunct challenge instance stack %s', stack)
                self.stacks.rm(stack)
                self.redis.delete(key)

    def create(self, challenge_id, user_id, stack, service, needs_flag=True, needs_gateway=False):
        result = {'id': self.ids.encode(challenge_id, user_id)}
        name = stack_name(challenge_id, user_id)
        if name in self.stacks.ls():
            raise ChallengeException(f'An instance of challenge ID {challenge_id} already exists for user ID {user_id}')

        stack_template = Template(json.dumps(stack))
        stack = json.loads(stack_template.substitute(chad_id=result['id']))

        dpath.new(stack, f'services/{service}/deploy/labels/{LABEL_PRIMARY}', 'true')
        if needs_flag:
            result['flag'] = self.flags.next_flag()
            secret_tmp = tempfile.NamedTemporaryFile('w', prefix='flag', suffix='.txt', encoding='ascii')
            secret_tmp.write(f'{result["flag"]}\n')
            secret_tmp.flush()

            dpath.new(stack, f'secrets/flag/file', secret_tmp.name)
            dpath.merge(stack, {'services': {service: {'secrets': [{
                'source': 'flag',
                'target': 'flag.txt',
                'mode': 0o440
            }]}}})

        self.redis.set(f'{name}_last_ping', int(time.time()))
        self.stacks.deploy(name, stack, registry_auth=True)
        if needs_flag:
            secret_tmp.close()
        return result

    def ping(self, challenge_id, user_id):
        name = stack_name(challenge_id, user_id)
        if name not in self.stacks.ls():
            raise ChallengeException(f'An instance of challenge ID {challenge_id} does not exist for user ID {user_id}')

        self.redis.set(f'{name}_last_ping', int(time.time()))

    def reset(self, challenge_id, user_id):
        services = self.docker.services.list(filters={
            'label': [
                f'com.docker.stack.namespace={stack_name(challenge_id, user_id)}'
            ]
        })
        if not services:
            raise ChallengeException(f'An instance of challenge ID {challenge_id} does not exist for user ID {user_id}')

        for service in services:
            service.force_update()

    def delete(self, challenge_id, user_id):
        name = stack_name(challenge_id, user_id)
        if name not in self.stacks.ls():
            raise ChallengeException(f'An instance of challenge ID {challenge_id} does not exist for user ID {user_id}')

        self.stacks.rm(name)
