import time
import logging

import dpath.util as dpath
import hashids

from . import util

LABEL_PREFIX = 'org.hacktrinity.chad'

class ChallengeManager:
    def __init__(self, docker, stacks, salt, flag_prefix='CTF'):
        self.ids = hashids.Hashids(salt, min_length=8)
        self.flags = util.FlagGenerator(prefix=flag_prefix)

        self.docker = docker
        self.stacks = stacks

    def create(self, challenge_id, user_id, stack, service, needs_flag=True, needs_gateway=False):
        result = {'id': self.ids.encode(challenge_id, user_id)}
        name = f'chad_{result["id"]}'
        dpath.new(stack, f'services/{service}/deploy/labels/{LABEL_PREFIX}.last-ping', int(time.time()))
        if needs_flag:
            secret = f'{name}_flag'
            result['flag'] = self.flags.next_flag()
            self.docker.secrets.create(name=secret, data=result['flag'].encode('ascii'))
            dpath.new(stack, f'secrets/{secret}/external', True)
            dpath.merge(stack, {'services': {service: {'secrets': [secret]}}})

        self.stacks.deploy(name, stack, registry_auth=True)
        return result

    def delete(self, challenge_id, user_id):
        pass
