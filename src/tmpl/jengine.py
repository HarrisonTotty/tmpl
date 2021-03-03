#!/usr/bin/env python3
'''
Contains code pertaining to creating the Jinja2 engine.
'''

import importlib.util
import inspect
import jinja2
import logging
import os

from . import jfuncs

def import_lib(jinja_engine, path: str):
    '''
    Imports functions from the specified file path into the specified Jinja
    engine.
    '''
    modname = os.path.basename(path).split('.', 1)[0]
    logging.debug(f'Importing library at "{path}" as "{modname}"...')
    if not os.path.isfile(path):
        raise Exception('library extension file at "{path}" does not exist')
    try:
        spec = importlib.util.spec_from_file_location(modname, path)
    except Exception as e:
        raise Exception(f'unable to generate importlib spec from "{modname}" at "{path}" - {e}')
    try:
        mod = importlib.util.module_from_spec(spec)
    except Exception as e:
        raise Exception(f'unable to convert importlib spec of "{modname}" to module object - {e}')
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        raise Exception(f'unable to execute module "{modname}" - {e}')
    for f in inspect.getmembers(mod, inspect.isfunction):
        logging.debug('Importing module function "{f[0]}"...')
        jinja_engine.globals[f[0]] = f[1]


def setup(args, template_dir: str):
    '''
    Creates a new Jinja2 engine.
    '''
    logging.debug('Initializing Jinja2 file system loader...')
    try:
        fsloader = jinja2.FileSystemLoader(template_dir)
    except Exception as e:
        raise Exception(f'unable to initialize jinja2 file system loader - {e}')
    logging.debug('Initializing Jinja2 engine...')
    jinja_engine = jinja2.Environment(
        block_end_string      = args.block_end_string,
        block_start_string    = args.block_start_string,
        comment_end_string    = args.comment_end_string,
        comment_start_string  = args.comment_start_string,
        extensions            = ['jinja2.ext.do', 'jinja2.ext.loopcontrols'],
        loader                = fsloader,
        trim_blocks           = args.trim_jinja_blocks,
        variable_end_string   = args.variable_end_string,
        variable_start_string = args.variable_start_string
    )
    logging.debug('Importing custom Jinja functions...')
    for f in inspect.getmembers(jfuncs, inspect.isfunction):
        if f[0].startswith('t_'):
            jname = f[0].split('_', 1)[1]
            logging.debug(f'Importing custom function "{f[0]}" as "{jname}"...')
            jinja_engine.globals[jname] = f[1]
    return jinja_engine
