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

    body = {
        'user_id': args.user_id,
        'challenge_id': args.challenge_id,
        'stack': stack,
        'service': args.service,
        'flag': args.flag
    }
    res = requests.post(f'{args.host}/instances', json=body)
    pfallback(res)

def ping(args):
    res = requests.patch(f'{args.host}/instances/{args.user_id}/{args.challenge_id}')
    if res.status_code != 204:
        pfallback(res)

def reset(args):
    res = requests.put(f'{args.host}/instances/{args.user_id}/{args.challenge_id}')
    if res.status_code != 204:
        pfallback(res)

def delete(args):
    res = requests.delete(f'{args.host}/instances/{args.user_id}/{args.challenge_id}')
    if res.status_code != 204:
        pfallback(res)

def main():
    parser = argparse.ArgumentParser(description='Test client for CHAD')
    parser.add_argument('-H', '--host', default='http://localhost:8001', help='CHAD server base URL')

    commands = parser.add_subparsers(required=True, dest='command')

    c_create = commands.add_parser('create', help='Create challenge')
    c_create.set_defaults(fn=create)
    c_create.add_argument('-u', '--user-id', type=int, default=1, help='User ID')
    c_create.add_argument('-c', '--challenge-id', type=int, default=1, help='Challenge ID')
    c_create_flag = c_create.add_mutually_exclusive_group()
    c_create_flag.add_argument('-r', '--no-random-flag', action='store_false', dest='flag',
        help='Don\'t request flag')
    c_create_flag.add_argument('-f', '--flag', help='Flag to use')
    c_create.add_argument('stack', help='Path to stack YAML')
    c_create.add_argument('service', help='Primary challenge service')

    c_ping = commands.add_parser('ping', help='Ping challenge')
    c_ping.set_defaults(fn=ping)
    c_ping.add_argument('-u', '--user-id', type=int, default=1, help='User ID')
    c_ping.add_argument('-c', '--challenge-id', type=int, default=1, help='Challenge ID')

    c_reset = commands.add_parser('reset', help='Reset challenge')
    c_reset.set_defaults(fn=reset)
    c_reset.add_argument('-u', '--user-id', type=int, default=1, help='User ID')
    c_reset.add_argument('-c', '--challenge-id', type=int, default=1, help='Challenge ID')

    c_delete = commands.add_parser('delete', help='Delete challenge')
    c_delete.set_defaults(fn=delete)
    c_delete.add_argument('-u', '--user-id', type=int, default=1, help='User ID')
    c_delete.add_argument('-c', '--challenge-id', type=int, default=1, help='Challenge ID')

    args = parser.parse_args()
    args.fn(args)

if __name__ == '__main__':
    main()
