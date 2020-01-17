import subprocess
import json

class StackManager:
    def __init__(self, sock='unix:///run/docker.sock'):
        self.sock = sock

    def docker_cmd(self, args, *e_args, parse=True, **kwargs):
        lines = filter(lambda l: l, subprocess.check_output(['docker', '--host', self.sock] + args, *e_args,
            encoding='utf-8', **kwargs).split('\n'))

        if parse:
            return map(json.loads, lines)
        return lines

    def list_all(self):
        return list(self.docker_cmd(['stack', 'ls', '--format', '{{json .}}']))

    def services(self, id_):
        return list(self.docker_cmd(['stack', 'services', '--format', '{{json .}}', id_]))
