import string
import os
from os import path
import subprocess
import ipaddress

class EasyRSAError(Exception):
    pass

class EasyRSA:
    def __init__(self, id_, name, directory, easyrsa='/usr/share/easy-rsa', days=3650, dn=None, existing_dh=None):
        self.id = id_
        self.name = name
        self.dir = path.abspath(directory)
        self.easyrsa = easyrsa
        self.days = days
        self.dn = {
            'country': 'IE',
            'state': 'Dublin',
            'city': 'Dublin',
            'org': 'Netsoc',
            'ou': 'HackTrinity',
            'email': 'admin@hacktrinity.org'
        }
        if dn:
            self.dn.update(dn)

        if not path.exists(self.dir):
            self._cmd('init-pki')

        dh_path = path.join(self.dir, 'dh.pem')
        if not path.exists(dh_path):
            if existing_dh:
                os.symlink(existing_dh, dh_path)
            else:
                self.gen_dh()

    def _cmd(self, command, options=None, cn=None, dn_org=False, **proc_options):
        try:
            args = ['easyrsa', '--batch', f'--pki-dir={self.dir}', f'--days={self.days}']
            if dn_org:
                args += [
                    '--dn-mode=org',
                    f'--req-c={self.dn["country"]}',
                    f'--req-st={self.dn["state"]}',
                    f'--req-city={self.dn["city"]}',
                    f'--req-org={self.dn["org"]}',
                    f'--req-email={self.dn["email"]}',
                    f'--req-ou={self.dn["ou"]}'
                ]
            else:
                args.append('--dn-mode=cn_only')

            if cn:
                args.append(f'--req-cn={cn}')

            args.append(command)

            if options:
                if isinstance(options, str):
                    args.append(options)
                else:
                    args += options

            env = dict(os.environ)
            env['EASYRSA'] = self.easyrsa
            subprocess.check_call(args, env=env, stderr=subprocess.STDOUT, **proc_options)
        except subprocess.CalledProcessError as ex:
            raise EasyRSAError(f'easyrsa non-zero exit code {ex.returncode}: {ex.output}')

    def gen_ovpn_key(self):
        ta_path = path.join(self.dir, 'ta.key')
        if path.exists(ta_path):
            return ta_path

        subprocess.check_call(['openvpn', '--genkey', '--secret', ta_path])
        return ta_path

    def gen_dh(self):
        self._cmd('gen-dh')

    def build_ca(self):
        if path.exists(path.join(self.dir, 'ca.crt')):
            return
        self._cmd('build-ca', 'nopass', cn=self.name, dn_org=True)

    def req_sub_ca(self):
        self._cmd('build-ca', ['nopass', 'subca'], cn=self.name, dn_org=True)
        return path.join(self.dir, 'reqs/ca.req')

    def build_child_ca(self, child):
        child_ca_path = path.join(child.dir, 'ca.crt')
        if path.exists(child_ca_path):
            return False

        req_name = f'{child.id}_ca'
        req_path = child.req_sub_ca()

        self._cmd('import-req', [req_path, req_name])
        self._cmd('sign-req', ['ca', req_name])
        os.symlink(path.join(self.dir, 'issued', f'{req_name}.crt'), child_ca_path)
        return True

    def build_full(self, type_, name):
        cert_path = path.join(self.dir, 'issued', f'{name}.crt')
        key_path = path.join(self.dir, 'private', f'{name}.key')
        if path.exists(cert_path):
            return cert_path, key_path

        self._cmd(f'build-{type_}-full', [name, 'nopass'])
        return cert_path, key_path
    def build_server(self, name='server'):
        return self.build_full('server', name)
    def build_client(self, name='client'):
        return self.build_full('client', name)

class PKI:
    def __init__(self, directory='/etc/chad_pki', easyrsa='/usr/share/easy-rsa', domain='chad-gw.sys.hacktrinity.org',
        dn=None):
        self.dir = directory
        self.domain = domain
        self.root = EasyRSA('chad_root', 'HackTrinity CHAD Root CA', path.join(self.dir, 'root'),
            easyrsa=easyrsa, dn=dn)
        self.root.build_ca()

        with open('CHAD/ovpn_server.conf.tpl') as tpl_file:
            self.server_template = string.Template(tpl_file.read())
        with open('CHAD/ovpn_client.conf.tpl') as tpl_file:
            self.client_template = string.Template(tpl_file.read())
        self.users = {}

    def _get_user(self, user_id):
        id_ = f'user_{user_id}'
        if user_id not in self.users:
            rsa = EasyRSA(id_, f'HackTrinity CHAD User {user_id} CA', path.join(self.dir, id_),
                easyrsa=self.root.easyrsa, dn=self.root.dn, existing_dh=path.join(self.root.dir, 'dh.pem'))
            self.root.build_child_ca(rsa)
            rsa.gen_ovpn_key()
            self.users[user_id] = rsa
            self.get_server(user_id)
            self.get_client(user_id)
        return self.users[user_id]

    def get_server(self, user_id):
        return self._get_user(user_id).build_server(f'{user_id}.{self.domain}')
    def get_client(self, user_id):
        return self._get_user(user_id).build_client()

    def _read_user_file(self, user_id, p):
        rsa = self._get_user(user_id)
        with open(path.join(rsa.dir, p)) as f:
            return f.read()
    def generate_server_ovpn(self, user_id, pool_start, pool_end, network):
        return self.server_template.substitute(
            pool=f'{pool_start} {pool_end} {ipaddress.IPv4Network(network).netmask}',
            ca=self._read_user_file(user_id, 'ca.crt'),
            cert=self._read_user_file(user_id, f'issued/{user_id}.{self.domain}.crt'),
            key=self._read_user_file(user_id, f'private/{user_id}.{self.domain}.key'),
            dh=self._read_user_file(user_id, f'dh.pem'),
            ta_key=self._read_user_file(user_id, f'ta.key'))
    def generate_client_ovpn(self, user_id):
        return self.client_template.substitute(
            ca=self._read_user_file(user_id, 'ca.crt'),
            cert=self._read_user_file(user_id, f'issued/{user_id}.{self.domain}.crt'),
            key=self._read_user_file(user_id, f'private/{user_id}.{self.domain}.key'),
            ta_key=self._read_user_file(user_id, f'ta.key'),
            server=f'{user_id}.{self.domain}',
            proxy=self.domain)
