#!/usr/bin/env python3

import glob
import logging
import os
import pathlib
import re
import socket
import subprocess
import sys
from typing import Any

LIST_REGEX = re.compile(
    r'^[/\w\.\-\ ]*(?P<expr>\[(?P<inner>[/\w\.\-\ ,]+)\])[/\w\.\-\ ]*$'
)
RANGE_REGEX = re.compile(
    r'^[/\w\.\-\ ]*(?P<expr>\[(?P<lower>\d+)\-(?P<upper>\d+)\])[/\w\.\-\ ]*$'
)
TEMPLATE_DIR = ''


def get_hostname() -> tuple[str, str]:
    '''
    Obtains the hostname and FQDN of the executing machine.
    '''
    return (
        socket.gethostname().split('.', 1)[0],
        socket.getfqdn()
    )


def get_path(template_path: str, base_path: str = '') -> str:
    '''
    Returns the full path to a file specified in the template configuration file.
    '''
    if template_path.startswith('/'):
        return template_path
    elif template_path.startswith('~'):
        return os.path.expanduser(template_path)
    else:
        if base_path:
            if '../' in base_path:
                return os.path.abspath(os.path.join(base_path, template_path))
            else:
                return os.path.normpath(os.path.join(base_path, template_path))
        else:
            return os.path.normpath(os.path.join(TEMPLATE_DIR, template_path))


def merge_yaml_data(data1: Any, data2: Any) -> Any:
    '''
    Returns the recursively-merged version of both YAML data objects.
    The second object has priority on conflicts.
    '''
    if isinstance(data1, str) and isinstance(data2, str):
        return data2
    if isinstance(data1, list) and isinstance(data2, list):
        return_list = data1.copy()
        return_list.extend(data2.copy())
        return return_list
    if isinstance(data1, dict) and isinstance(data2, dict):
        return_dict = data1.copy()
        for key, val in data2.items():
            if key in return_dict:
                return_dict[key] = merge_yaml_data(return_dict[key], val)
            else:
                return_dict[key] = val
        return return_dict
    return data2


def parse_file_paths(path_spec: str) -> list[str]:
    '''
    Returns the equivalent list of file paths given a path specification.
    With the exception of globbing, the resulting paths are only computed and
    are not checked to be valid. If a glob results in no files, an empty list is
    returned.

    Examples:
    /foo/bar1.txt      ->  [/foo/bar1.txt]
    /foo/bar*.txt      ->  [/foo/bar1.txt, /foo/bar2.txt, ...]
    /foo/bar[1,2].txt  ->  [/foo/bar1.txt, /foo/bar2.txt]
    /foo/bar[1-3].txt  ->  [/foo/bar1.txt, /foo/bar2.txt, /foo/bar3.txt]
    '''
    if not '*' in path_spec and not '[' in path_spec and not ']' in path_spec:
        return [path_spec]
    elif '*' in path_spec:
        try:
            if not '**' in path_spec:
                return glob.glob(path_spec)
            elif path_spec.startswith('/'):
                base_path = '/'
                altered_path_spec = path_spec.lstrip('/')
            else:
                base_path = '.'
                altered_path_spec = path_spec
            return [f.as_posix() for f in pathlib.Path(base_path).glob(altered_path_spec) if f.is_file()]
        except Exception as e:
            raise Exception(f'path specification globbing encountered an exception - {e}')
    elif '[' in path_spec and ']' in path_spec:
        paths = []
        guts = path_spec.split('[', 1)[1]
        if not ']' in guts:
            raise Exception('path specification has its shoelaces crossed')
        guts = guts.split(']', 1)[0]
        if ',' in guts:
            list_match = LIST_REGEX.match(path_spec)
            if not list_match:
                raise Exception('path specification does not contain a valid list expression')
            expr = list_match.group('expr')
            parts = expr[1:-1].split(',')
            for p in parts:
                if p:
                    paths.append(path_spec.replace(expr, p))
        elif '-' in guts:
            range_match = RANGE_REGEX.match(path_spec)
            if not range_match:
                raise Exception('path specification does not contain a valid range expression')
            expr = range_match.group('expr')
            lb = int(range_match.group('lower'))
            ub = int(range_match.group('upper'))
            if not ub > lb:
                raise Exception('upperbound in path specification range expression is not greater than the lowerbound')
            for i in range(lb, ub + 1):
                paths.append(path_spec.replace(expr, str(i)))
        else:
            raise Exception('path specification does not specify a range or list expression')
        return paths
    else:
        raise Exception('path specification does not have balanced brackets')


def run_process(cmd: str, splitlines=True) -> tuple:
    '''
    Runs the specified command as a subprocess, returning the output of the
    command (optionally not split by lines) and its exit code.
    '''
    process = subprocess.Popen(
        cmd,
        stdout = subprocess.PIPE,
        stderr = subprocess.STDOUT,
        shell = True
    )
    output = process.communicate()[0].decode('ascii', 'ignore')
    exit_code = process.returncode
    if splitlines:
        return (output.splitlines(), exit_code)
    else:
        return (output, exit_code)


def setup_logging(args: Any):
    '''
    Sets-up logging.
    '''
    if args.log_file:
        try:
            if args.log_mode == 'append':
                logging_fmode = 'a'
            else:
                logging_fmode = 'w'
            if args.log_level == 'info':
                logging_level = logging.INFO
            else:
                logging_level = logging.DEBUG
            logging.basicConfig(
                filename = args.log_file,
                filemode = logging_fmode,
                level    = logging_level,
                format   = '[%(levelname)s] [%(asctime)s] [%(process)d] [%(module)s.%(funcName)s] %(message)s',
                datefmt  = '%m/%d/%Y %I:%M:%S %p'
            )
            logging.addLevelName(logging.CRITICAL, 'CRI')
            logging.addLevelName(logging.ERROR, 'ERR')
            logging.addLevelName(logging.WARNING, 'WAR')
            logging.addLevelName(logging.INFO, 'INF')
            logging.addLevelName(logging.DEBUG, 'DEB')
        except Exception as e:
            sys.exit('Unable to initialize logging system - ' + str(e) + '.')
    else:
        logger = logging.getLogger()
        logger.disabled = True
