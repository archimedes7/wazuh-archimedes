#!/var/ossec/framework/python/bin/python3

# Copyright (C) 2015-2019, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is a free software; you can redistribute it and/or modify it under the terms of GPLv2

import argparse
import ipaddress
import re
import sys

from api.constants import UWSGI_CONFIG_PATH, API_CONFIG_PATH, TEMPLATE_API_CONFIG_PATH

_ip_host = re.compile(r'( *)(# )?http:(.*):')
_proxy_value = re.compile(r'(.*)behind_proxy_server:(.*)')
_basic_auth_value = re.compile(r'(.*)basic_auth:(.*)')
_uwsgi_socket = re.compile(r'( *)(# )?shared-socket:(.*):')
_uwsgi_certs = re.compile(r'https: =(.*)')

new_api_yaml = False


def check_uwsgi_config():
    try:
        with open(UWSGI_CONFIG_PATH, 'r+'):
            return True
    except FileNotFoundError:
        print('[ERROR] uWSGI configuration file does not exists: {}'.format(UWSGI_CONFIG_PATH))

    return False


def check_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        print('[ERROR] Address/Netmask is invalid: {}'.format(ip))
    except Exception as e:
        print('[ERROR] There is a problem with the IP provided: \n{}'.format(e))

    return False


def check_port(port):
    if port is not None:
        if 1 <= port <= 65535:
            return True
        print('[ERROR] The port provided is invalid, the port must be a number between 1 and 65535')
    return False


def check_boolean(component, value):
    if value is not None:
        if (value.lower() == 'true' or value.lower() == 'yes') \
                or (value.lower() == 'false' or value.lower() == 'no'):
            return True
        print('[ERROR] Invalid value for {}: {}'.format(component, value))
    return False


def convert_boolean_to_string(value):
    return 'yes' if value.lower() == 'true' or value.lower() == 'yes' else 'no'


def change_ip(ip):
    if check_ip(ip):
        with open(UWSGI_CONFIG_PATH, 'r+') as f:
            lines = f.readlines()

        new_file = ''
        for line in lines:
            match = re.search(_ip_host, line)
            match_uwsgi = re.search(_uwsgi_socket, line)
            if match or match_uwsgi:
                match_split = line.split(':')
                new_file += match_split[0] + ': ' + ip + ':' + match_split[2]
            else:
                new_file += line
        if new_file != '':
            with open(UWSGI_CONFIG_PATH, 'w') as f:
                f.write(new_file)
            print('[INFO] IP changed correctly to \'{}\''.format(ip))


def change_port(port):
    if check_port(port):
        with open(UWSGI_CONFIG_PATH, 'r+') as f:
            lines = f.readlines()

        new_file = ''
        for line in lines:
            match = re.search(_ip_host, line)
            if match:
                match_split = line.split(':')
                new_file += match_split[0] + ': ' + match_split[1] + ':' + str(port) + '\n'
            else:
                new_file += line
        if new_file != '':
            with open(UWSGI_CONFIG_PATH, 'w') as f:
                f.write(new_file)
            print('[INFO] PORT changed correctly to \'{}\''.format(port))


def change_basic_auth(value):
    try:
        with open(API_CONFIG_PATH, 'r+') as f:
            lines = f.readlines()
    except FileNotFoundError:
        with open(TEMPLATE_API_CONFIG_PATH, 'r+') as f:
            lines = f.readlines()

    new_file = ''
    changed = False
    value = convert_boolean_to_string(value)
    for line in lines:
        match = re.search(_basic_auth_value, line)
        if match:
            match_split = line.split(':')
            comment = match_split[0].split('# ')
            if len(comment) > 1:
                match_split[0] = comment[1]
            if match_split[1].startswith(' yes') and value == 'no':
                changed = True
            new_file += match_split[0] + ': ' + value + '\n'
        else:
            new_file += line
    if new_file != '':
        with open(API_CONFIG_PATH, 'w') as f:
            f.write(new_file)
        if changed:
            print('[INFO] Basic auth value set to \'{}\''.format(value))


def change_proxy(value):
    try:
        with open(API_CONFIG_PATH, 'r+') as f:
            lines = f.readlines()
    except FileNotFoundError:
        with open(TEMPLATE_API_CONFIG_PATH, 'r+') as f:
            lines = f.readlines()

    new_file = ''
    for line in lines:
        match = re.search(_proxy_value, line)
        if match:
            match_split = line.split(':')
            comment = match_split[0].split('# ')
            if len(comment) > 1:
                match_split[0] = comment[1]
            new_file += match_split[0] + ': ' + value + '\n'
        else:
            new_file += line
    if new_file != '':
        with open(API_CONFIG_PATH, 'w') as f:
            f.write(new_file)
        print('[INFO] PROXY value changed correctly to \'{}\''.format(value))


def change_http(line, value):
    match_split = line.split(':')
    if value == 'yes':
        comment = match_split[0].split('# ')
        if len(comment) > 1:
            match_split[0] = comment[0] + comment[1]
    elif value == 'no' and '# ' not in ''.join(match_split):
        comment = match_split[0].split('h')
        if len(comment) > 1:
            match_split[0] = comment[0] + '# h' + comment[1]

    print('[INFO] HTTP changed correctly to \'{}\''.format(value))
    return ':'.join(match_split)


def change_https(value, https=True):
    with open(UWSGI_CONFIG_PATH, 'r+') as f:
        lines = f.readlines()

    value = convert_boolean_to_string(value)
    # Disable basic auth
    if value == 'yes' and https:
        change_basic_auth('no')

    new_file = ''
    for line in lines:
        match = re.search(_uwsgi_socket, line)
        match_cert = re.search(_uwsgi_certs, line)
        match_http = re.search(_ip_host, line)
        if match_http and not https:
            line = change_http(line, value)
            new_file += line
        elif https and (match or match_cert):
            match_split = line.split(':')
            if value == 'yes':
                comment = match_split[0].split('# ')
                if len(comment) > 1:
                    match_split[0] = comment[0] + comment[1]
            elif '# ' not in ''.join(match_split):  # If it is not already disable
                if match:
                    comment = match_split[0].split('sh')
                    if len(comment) > 1:
                        match_split[0] = comment[0] + '# sh' + comment[1]
                elif match_cert:
                    comment = match_split[0].split('h')
                    if len(comment) > 1:
                        match_split[0] = comment[0] + '# h' + comment[1]
            new_file += ':'.join(match_split)
        else:
            new_file += line
    if new_file != '':
        with open(UWSGI_CONFIG_PATH, 'w') as f:
            f.write(new_file)
        if https:
            print('[INFO] HTTPS changed correctly to \'{}\''.format(value))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port',     help="Change port number",                          type=int)
    parser.add_argument('-i', '--ip',       help="Change the host IP",                          type=str)
    parser.add_argument('-b', '--basic',    help="Configure basic authentication (true/false)", type=str)
    parser.add_argument('-x', '--proxy',    help="Yes to run API behind a proxy",               type=str)
    parser.add_argument('-t', '--http',     help="Enable http protocol (true/false)",           type=str)
    parser.add_argument('-s', '--https',    help="Enable https protocol (true/false)",          type=str)
    args = parser.parse_args()

    if check_uwsgi_config() and len(sys.argv) > 1:
        if args.ip:
            change_ip(args.ip)

        if args.port:
            change_port(args.port)

        if check_boolean('proxy', args.proxy):
            change_proxy(args.proxy)

        if check_boolean('basic auth', args.basic):
            change_basic_auth(args.basic)

        if check_boolean('https', args.https):
            change_https(args.https)

        if check_boolean('http', args.http):
            if args.http.lower() == 'true' or args.http.lower() == 'yes':
                args.http = 'yes'
            elif args.http.lower() == 'false' or args.http.lower() == 'no':
                args.http = 'no'
            change_https(args.http, https=False)
    elif len(sys.argv) == 1:
        parser.print_help()
    else:
        print('[ERROR] Please check that your configuration is correct')
