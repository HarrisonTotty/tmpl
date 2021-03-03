#!/usr/bin/env python3
'''
Contains the set of Jinja2 functions included with `tmpl`.
'''

import jinja2
import logging
import os
import socket
import yaml

from . import cli
from . import utils


def t_domain_join(*variables) -> str:
    '''
    A Jinja function that acts like os.path.join but with domain strings.
    '''
    return '.'.join([x.strip('.') for x in variables])


def t_env(name: str, default=None) -> str:
    '''
    A Jinja function that literally just calls os.getenv() under the hood.
    '''
    return os.getenv(name, default)


def t_file_ext(path: str) -> str:
    '''
    A Jinja function that returns the file extension of the specified path.
    '''
    basename = os.path.basename(path)
    if not '.' in basename:
        return ''
    else:
        return basename.split('.', 1)[1]


def t_file_name(path: str) -> str:
    '''
    A Jinja function that returns the file name (without the extension) of the
    specified path.
    '''
    basename = os.path.basename(path)
    if not '.' in basename:
        return basename
    else:
        return basename.split('.', 1)[0]


@jinja2.contextfunction
def t_get(context, variable: str):
    '''
    A Jinja function that returns the value of the specified variable string name.
    '''
    try:
        return context.resolve(variable)
    except Exception as e:
        raise Exception(f'get() : Unable to fetch value of "{variable}" - {e}')


def t_get_host(ip: str) -> str:
    '''
    A Jinja function that returns the host of a particular IP.
    '''
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception as e:
        raise Exception(f'get_host() : Unable to obtain host for specified IP address "{ip}" - {e}')


def t_get_ip(host: str) -> str:
    '''
    A Jinja function that returns the IP of a particular host.
    '''
    try:
        return socket.gethostbyname(host)
    except Exception as e:
        raise Exception(f'get_ip() : Unable to obtain IP address for specified host "{host}" - {e}')


def t_get_output(cmd: str) -> str:
    '''
    A Jinja function that returns the output of the specified command.
    '''
    try:
        return utils.run_process(cmd, splitlines=False)[1]
    except Exception as e:
        raise Exception(f'get_output() : Unable to get output from command "{cmd}" - {e}')


def t_parse_yaml(yaml_str: str) -> str:
    '''
    A Jinja function that parses the specified YAML string.
    '''
    try:
        return yaml.safe_load(yaml_str)
    except Exception as e:
        raise Exception(f'parse_yaml() : Unable to parse YAML string - {e}')


def t_path_basename(path: str) -> str:
    '''
    Wrapper around `os.path.basename`.
    '''
    try:
        os.path.basename(path)
    except Exception as e:
        raise Exception(f'path_basename() : {e}')


def t_path_dirname(path: str) -> str:
    '''
    Wrapper around `os.path.dirname`.
    '''
    try:
        os.path.dirname(path)
    except Exception as e:
        raise Exception(f'path_dirname() : {e}')


def t_path_join(*paths) -> str:
    '''
    Wrapper around `os.path.join`.
    '''
    try:
        os.path.join(*paths)
    except Exception as e:
        raise Exception(f'path_join() : {e}')


def t_print(message):
    '''
    A Jinja function that prints and logs the specified message or object.
    '''
    logging.info(str(message))
    cli.stdout(cli.fsubsubstep(str(message), cli.C_BLUE))


def t_raise(message: str):
    '''
    A Jinja function that raises an exception with the supplied message.
    '''
    raise Exception(f'raise() : {message}')


def t_read_file(path: str) -> str:
    '''
    Returns the contents of the file located at the specified path, relative to
    the path to the template configuration file.
    '''
    actual_path = utils.get_path(path)
    if not os.path.isfile(actual_path):
        raise Exception(f'read_file() : Cannot read file "{actual_path}" - specified file path does not exist')
    try:
        with open(actual_path, 'r') as f:
            contents = f.read()
    except Exception as e:
        raise Exception(f'read_file() : Cannot read file "{actual_path}" - {e}')
    return contents


@jinja2.contextfunction
def t_require(context, *variables):
    '''
    A Jinja filter which specifies that the specified variables are required.

    See:
    http://jinja.pocoo.org/docs/2.10/api/#the-context
    http://jinja.pocoo.org/docs/2.10/api/#jinja2.contextfilter
    '''
    for variable in variables:
        if '.' in variable:
            splitvar = variable.split('.', 1)
            if not splitvar[0] in context:
                raise Exception(f'require() : Required variable "{splitvar[0]}" not found in within the context of "{context.name}"')
            if not splitvar[1] in context[splitvar[0]]:
                raise Exception(f'require() : Required variable "{variable}" not found in within the context of "{context.name}"')
        else:
            if not variable in context:
                raise Exception(f'require() : Required variable "{variable}" not found in within the context of "{context.name}"')
