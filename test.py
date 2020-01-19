#!/usr/bin/env python
import argparse
from pprint import pprint

import yaml
import requests

def pfallback(res):
    if res.headers['content-type'].startswith('application/json'):
        pprint(res.json())
    else:
        print(res.text)

def create(args):
    with open(args.stack) as stack_file:
        stack = yaml.safe_load(stack_file)

    res = requests.post(f'{args.host}/instances', json={
        'challenge_id': args.challenge_id,
        'user_id': args.user_id,
        'stack': stack,
        'service': args.service,
        'needs_flag': args.needs_flag,
        'needs_gateway': args.needs_gateway
    })
    pfallback(res)

def main():
    parser = argparse.ArgumentParser(description='Test client for CHAD')
    parser.add_argument('-H', '--host', default='http://localhost:8001', help='CHAD server base URL')

    commands = parser.add_subparsers(required=True, dest='command')

    c_create = commands.add_parser('create', help='Create challenge')
    c_create.set_defaults(fn=create)
    c_create.add_argument('-c', '--challenge-id', type=int, default=1, help='Challenge ID')
    c_create.add_argument('-u', '--user-id', type=int, default=1, help='User ID')
    c_create.add_argument('-f', '--without-flag', action='store_false', dest='needs_flag', help='Request flag')
    c_create.add_argument('-g', '--with-gateway', action='store_true', dest='needs_gateway', help='Request gateway')
    c_create.add_argument('stack', help='Path to stack YAML')
    c_create.add_argument('service', help='Primary challenge service')

    args = parser.parse_args()
    args.fn(args)

if __name__ == '__main__':
    main()
