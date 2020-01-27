from string import Template
import re
import json
import tempfile
import time
import ipaddress

import dpath.util as dpath
import hashids
import docker

from . import util, pki

LABEL_PREFIX = 'org.hacktrinity.chad'

NETWORK = ipaddress.IPv4Network('192.168.128.0/17')
POOL_START = ipaddress.IPv4Address('192.168.255.1')
POOL_END = ipaddress.IPv4Address('192.168.255.254')

GATEWAY_SERVICE_REGEX = re.compile('chad_(\\d+)_gw$')

def stack_name(u, c):
    return f'chad_{u}_{c}'

class ChallengeException(Exception):
    pass

class ChallengeManager:
    def __init__(self, docker_, pki_: pki.PKI, stacks, redis, salt, docker_registry='example.com', flag_prefix='CTF',
        instance_timeout=60, gateway_timeout=120, gateway_image='chad-gateway',
        gateway_domain='chad-gw.sys.hacktrinity.org', traefik_network='traefik'):
        self.ids = hashids.Hashids(salt, min_length=10)
        self.flags = util.FlagGenerator(prefix=flag_prefix)

        self.docker = docker_
        self.pki = pki_
        self.stacks = stacks
        self.redis = redis
        self.instance_timeout = instance_timeout
        self.gateway_timeout = gateway_timeout
        self.docker_registry = docker_registry
        self.gateway_image = gateway_image
        self.gateway_domain = gateway_domain
        self.traefik_network = self.docker.networks.get(traefik_network)

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
            if now - last > self.instance_timeout:
                if logger:
                    logger.info('cleaning up defunct challenge instance stack %s', stack)
                self.stacks.rm(stack)
                self.redis.delete(key)

        gateways = self.docker.services.list(filters={
            'label': [
                f'{LABEL_PREFIX}.is_gateway=true'
            ]
        })
        for service in gateways:
            user_id = int(GATEWAY_SERVICE_REGEX.match(service.name).group(1))

            key = f'{service.name}_last_ping'
            last = self.redis.get(key)
            if last is None:
                # Give a chance for an untracked gateway to be pinged
                self.redis.set(key, now)
                continue

            last = int(last)
            if now - last > self.gateway_timeout:
                try:
                    self.ensure_gateway_gone(user_id)

                    if logger:
                        logger.info('cleaned up defunct gateway for user %d', user_id)
                    self.redis.delete(key)
                except ChallengeException:
                    logger.debug('NOT cleaning up defunct gateway for user %d (instances still running)', user_id)

    def ensure_gateway_up(self, user_id):
        service_name = f'chad_{user_id}_gw'
        try:
            self.docker.services.get(service_name)
            self.redis.set(f'chad_{user_id}_gw_last_ping', int(time.time()))
        except docker.errors.NotFound:
            net_name = f'chad_{user_id}'
            try:
                net = self.docker.networks.get(net_name)
            except docker.errors.NotFound:
                self.docker.networks.create(net_name, driver='weaveworks/net-plugin:latest_release')
                net = self.docker.networks.get(net_name)

            conf_secret_name = f'chad_{user_id}_gwconf'
            try:
                conf_secret = self.docker.secrets.get(conf_secret_name)
            except docker.errors.NotFound:
                conf = self.pki.generate_server_ovpn(user_id, POOL_START, POOL_END, NETWORK)
                self.docker.secrets.create(name=conf_secret_name, data=conf)
                conf_secret = self.docker.secrets.get(conf_secret_name)

            self.docker.services.create(self.gateway_image, name=service_name, env=['__CAP_ADD=NET_ADMIN'], labels={
                    f'{LABEL_PREFIX}.is_gateway': 'true',
                    'traefik.enable': 'true',
                    f'traefik.tcp.routers.chad_{user_id}_gw.rule':
                        f'HostSNI(`CONNECT:{user_id}.{self.gateway_domain}:1194`)',
                    f'traefik.tcp.routers.chad_{user_id}.entrypoints': 'http',
                    f'traefik.tcp.services.chad_{user_id}.loadbalancer.server.port': '1194'
                }, networks=[net.id, self.traefik_network.id],
                secrets=[docker.types.SecretReference(conf_secret.id, conf_secret_name, filename='server.conf',
                mode=0o440)])
            self.redis.set(f'chad_{user_id}_gw_last_ping', int(time.time()))

    def ensure_gateway_gone(self, user_id):
        regex = re.compile(f'chad_{user_id}_\\d+$')
        for stack in self.stacks.ls():
            if regex.match(stack):
                raise ChallengeException(f'Cannot destroy gateway for user {user_id}, challenge instances are running')

        try:
            self.docker.services.get(f'chad_{user_id}_gw').remove()
        except docker.errors.NotFound:
            pass

        try:
            self.docker.secrets.get(f'chad_{user_id}_gwconf').remove()
        except docker.errors.NotFound:
            pass

        try:
            self.docker.networks.get(f'chad_{user_id}').remove()
        except docker.errors.NotFound:
            pass

    def create(self, user_id, challenge_id, stack, service, needs_flag=True):
        result = {'id': self.ids.encode(user_id, challenge_id)}
        name = stack_name(user_id, challenge_id)
        if name in self.stacks.ls():
            raise ChallengeException(f'An instance of challenge ID {challenge_id} already exists for user ID {user_id}')

        self.ensure_gateway_up(user_id)

        stack_context = {
            'chad_id': result['id'],
            'chad_docker_registry': self.docker_registry
        }

        stack_template = Template(json.dumps(stack))
        stack = json.loads(stack_template.safe_substitute(**stack_context))

        # Docker Swarm overlay networks don't FUCKING SUPPORT MULTICAST
        dpath.new(stack, f'networks/challenge', {
            'driver': 'weaveworks/net-plugin:latest_release',
            'external': True,
            'name': f'chad_{user_id}'
        })
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
        if needs_flag:
            secret_tmp.close()
        return result

    def ping(self, user_id, challenge_id):
        name = stack_name(user_id, challenge_id)
        if name not in self.stacks.ls():
            raise ChallengeException(f'An instance of challenge ID {challenge_id} does not exist for user ID {user_id}')

        now = int(time.time())
        self.redis.set(f'chad_{user_id}_gw_last_ping', now)
        self.redis.set(f'{name}_last_ping', now)

    def reset(self, user_id, challenge_id):
        services = self.docker.services.list(filters={
            'label': [
                f'com.docker.stack.namespace={stack_name(user_id, challenge_id)}'
            ]
        })
        if not services:
            raise ChallengeException(f'An instance of challenge ID {challenge_id} does not exist for user ID {user_id}')

        for service in services:
            service.force_update()

    def delete(self, user_id, challenge_id):
        name = stack_name(user_id, challenge_id)
        if name not in self.stacks.ls():
            raise ChallengeException(f'An instance of challenge ID {challenge_id} does not exist for user ID {user_id}')

        self.stacks.rm(name)
