import subprocess
import json

class StackManager:
    def __init__(self, sock='unix:///run/docker.sock'):
        self.sock = sock

    def _docker_cmd(self, args, *e_args, parse=True, **kwargs):
        lines = filter(lambda l: l, subprocess.check_output(['docker', '--host', self.sock] + args, *e_args,
            encoding='utf-8', **kwargs).split('\n'))

        if parse:
            return map(json.loads, lines)
        return lines

    def ls(self):
        return list(map(lambda s: s['Name'], self._docker_cmd(['stack', 'ls', '--format', '{{json .}}'])))

    def services(self, id_):
        return list(self._docker_cmd(['stack', 'services', '--format', '{{json .}}', id_]))

    def deploy(self, name, spec, prune=False, registry_auth=False):
        args = ['stack', 'deploy', '--compose-file', '-']
        if prune:
            args.append('--prune')
        if registry_auth:
            args.append('--with-registry-auth')
        args.append(name)

        self._docker_cmd(args, input=json.dumps(spec), parse=False)
