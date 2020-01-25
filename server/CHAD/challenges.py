from string import Template
import json
import tempfile
import time
import secrets
import ipaddress

import yaml
import dpath.util as dpath
import hashids

from . import util

LABEL_PREFIX = 'org.hacktrinity.chad'
LABEL_PRIMARY = f'{LABEL_PREFIX}.primary'
CHALLENGE_NETWORK_START = 50

def stack_name(c, u):
    return f'chad_{c}_{u}'

class ChallengeException(Exception):
    pass

class ChallengeManager:
    def __init__(self, docker, stacks, redis, salt, docker_registry='example.com', flag_prefix='CTF', timeout=60,
        gateway_image='chad-gateway', gateway_proxy='chad-gw.sys.hacktrinity.org',
        challenge_domain='challs.hacktrinity.org', traefik_network='traefik'):
        self.ids = hashids.Hashids(salt, min_length=10)
        self.flags = util.FlagGenerator(prefix=flag_prefix)

        self.docker = docker
        self.stacks = stacks
        self.redis = redis
        self.timeout = timeout
        self.docker_registry = docker_registry
        self.gateway_image = gateway_image
        self.gateway_proxy = gateway_proxy
        self.challenge_domain = challenge_domain
        self.traefik_network = traefik_network

        with open('CHAD/gateway_service.yaml') as gw_service_file:
            self.gateway_service = yaml.safe_load(gw_service_file)

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

    @staticmethod
    def _net_to_pool(net):
        net = ipaddress.IPv4Network(net)
        start = util.nth(net, 50)
        if not start:
            raise ChallengeException(f'Network {net} is too small')

        *_, end, _broadcast = net
        return start, end, net.netmask

    def create(self, challenge_id, user_id, stack, service, needs_flag=True, gateway_network=None):
        result = {'id': self.ids.encode(challenge_id, user_id)}
        name = stack_name(challenge_id, user_id)
        if name in self.stacks.ls():
            raise ChallengeException(f'An instance of challenge ID {challenge_id} already exists for user ID {user_id}')

        stack_context = {
            'chad_id': result['id']
        }
        if gateway_network:
            start, end, mask = ChallengeManager._net_to_pool(gateway_network)

            stack_context.update({
                'chad_docker_registry': self.docker_registry,
                'chad_gateway_image': self.gateway_image,
                'chad_gateway_proxy': self.gateway_proxy,
                'chad_challenge_domain': self.challenge_domain,
                'chad_traefik_network': self.traefik_network,
                'chad_challenge_pool': f'{start} {end} {mask}'
            })

            config_password = secrets.token_urlsafe(16)
            result['gateway_config_password'] = config_password
            gw_password_tmp = tempfile.NamedTemporaryFile('w', prefix='gw_pwd', encoding='ascii')
            gw_password_tmp.write(f'{config_password}\n')
            gw_password_tmp.flush()

            dpath.new(stack, 'services/gateway', self.gateway_service)
            dpath.new(stack, f'networks/{self.traefik_network}/external', True)
            dpath.new(stack, 'secrets/config_password/file', gw_password_tmp.name)

        stack_template = Template(json.dumps(stack))
        stack = json.loads(stack_template.safe_substitute(**stack_context))

        # Docker Swarm overlay networks don't FUCKING SUPPORT MULTICAST
        dpath.new(stack, 'networks/default/driver', 'weaveworks/net-plugin:latest_release')
        dpath.new(stack, f'services/{service}/deploy/labels/{LABEL_PRIMARY}', 'true')
        if needs_flag:
            result['flag'] = self.flags.next_flag()
            secret_tmp = tempfile.NamedTemporaryFile('w', prefix='flag', suffix='.txt', encoding='ascii')
            secret_tmp.write(f'{result["flag"]}\n')
            secret_tmp.flush()

            dpath.new(stack, 'secrets/flag/file', secret_tmp.name)
            dpath.merge(stack, {'services': {service: {'secrets': [{
                'source': 'flag',
                'target': 'flag.txt',
                'mode': 0o440
            }]}}})

        self.redis.set(f'{name}_last_ping', int(time.time()))
        self.stacks.deploy(name, stack, registry_auth=True)
        if gateway_network:
            gw_password_tmp.close()
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
