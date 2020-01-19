from string import Template
import json
import time
import tempfile

import dpath.util as dpath
import hashids

from . import util

LABEL_PREFIX = 'org.hacktrinity.chad'

class ChallengeException(Exception):
    pass

class ChallengeManager:
    def __init__(self, docker, stacks, salt, flag_prefix='CTF'):
        self.ids = hashids.Hashids(salt, min_length=10)
        self.flags = util.FlagGenerator(prefix=flag_prefix)

        self.docker = docker
        self.stacks = stacks

    def create(self, challenge_id, user_id, stack, service, needs_flag=True, needs_gateway=False):
        result = {'id': self.ids.encode(challenge_id, user_id)}
        name = f'chad_{challenge_id}_{user_id}'
        if name in self.stacks.ls():
            raise ChallengeException(f'An instance of challenge ID {challenge_id} already exists for user ID {user_id}')

        stack_template = Template(json.dumps(stack))
        stack = json.loads(stack_template.substitute(chad_id=result['id']))

        dpath.new(stack, f'services/{service}/deploy/labels/{LABEL_PREFIX}.last-ping', int(time.time()))
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

        self.stacks.deploy(name, stack, registry_auth=True)
        if needs_flag:
            secret_tmp.close()
        return result

    def delete(self, challenge_id, user_id):
        name = f'chad_{challenge_id}_{user_id}'
        if name not in self.stacks.ls():
            raise ChallengeException(f'An instance of challenge ID {challenge_id} does not exist for user ID {user_id}')

        self.stacks.rm(name)
