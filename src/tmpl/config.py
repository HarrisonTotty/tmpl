#!/usr/bin/env python3
'''
Contains code pertaining to the template configuration file.
'''

import logging
import os
import yaml

from . import utils


def compute_mapping(conf: dict, output_dir: str, working_dir: str) -> list[dict]:
    '''
    Computes the file mappings and symlinks between template and output files.

    Each mapping is a list where the elements are a dictionary containing:

    chmod:     The "chmod" expression to set the resulting file to.
    chown:     The "chown" expression to set the resulting file to.
    dst_key:   The unparsed value of the "dst" key that produced this mapping.
    full_dst:  The full destination path relative to the output directory.
    full_lnk:  The full path to the resulting symlink destination, if applicable.
    full_src:  The full source path.
    full_wrk:  The full destination path relative to the working directory.
    rel_dst:   The relative destination path.
    rel_lnk:   The relative path to the resulting symlink destination, if applicable.
    rel_src:   The relative source path.
    translate: Whether to translate the file as a template.
    '''
    logging.debug('Computing path mapping...')
    mapping = []
    for spec in conf['files']:
        spec_dst = spec['dst']
        logging.debug(f'Computing template path mapping for "{spec_dst}"...')
        if 'src' in spec:
            logging.debug('TYPE: SRC')
            try:
                spec_full_srcs = utils.parse_file_paths(utils.get_path(spec['src']))
            except Exception as e:
                raise Exception(f'unable to compute template source path mapping for "{spec_dst}" - {e}')
            if not spec_full_srcs:
                raise Exception(f'unable to compute template source path mapping for "{spec_dst}" - "src" does not resolve to any valid source paths')
            spec_rel_srcs = [os.path.relpath(p, utils.TEMPLATE_DIR) for p in spec_full_srcs]
            for p in spec_full_srcs:
                if not os.path.exists(p):
                    raise Exception(f'unable to compute template source path mapping for "{spec_dst}" - "{p}" does not correspond to a path to an existing file')
            try:
                spec_full_dsts = utils.parse_file_paths(utils.get_path(spec_dst, output_dir))
            except Exception as e:
                raise Exception(f'unable to compute template destination path mapping for "{spec_dst}" - {e}')
            if not spec_full_dsts:
                raise Exception(f'unable to compute template destination path mapping for "{spec_dst}" - "dst" does not resolve to any valid destination paths')
            if len(spec_full_dsts) > 1:
                raise Exception(f'unable to compute template destination path mapping for "{spec_dst}" - "dst" cannot contain expansion expressions if "src" is specified')
            spec_full_dst = spec_full_dsts[0]
            spec_rel_dst = os.path.relpath(spec_full_dst, output_dir)
            spec_full_wrk = os.path.join(working_dir, spec_rel_dst)
            if 'symlink' in spec:
                if len(spec_full_srcs) > 1:
                    raise Exception('unable to compute template symlink path mapping for "{spec_dst}" - "symlink" cannot be specified if "src" contains expansion expressions')
                    spec_full_lnk = utils.get_path(spec['symlink'], output_dir)
                    spec_rel_lnk = os.path.relpath(spec_full_lnk, output_dir)
            else:
                spec_full_lnk = ''
                spec_rel_lnk = ''
            for (full_src, rel_src) in zip(spec_full_srcs, spec_rel_srcs):
                mapping.append({
                    'chmod':     spec['chmod'] if 'chmod' in spec else '',
                    'chown':     spec['chown'] if 'chown' in spec else '',
                    'dst_key':   spec_dst,
                    'full_dst':  spec_full_dst,
                    'full_lnk':  spec_full_lnk,
                    'full_src':  full_src,
                    'full_wrk':  spec_full_wrk,
                    'rel_dst':   spec_rel_dst,
                    'rel_lnk':   spec_rel_lnk,
                    'rel_src':   rel_src,
                    'translate': spec['translate'] if 'translate' in spec else True
                })
        else:
            logging.debug('TYPE: DST')
            try:
                spec_full_srcs = utils.parse_file_paths(utils.get_path(spec_dst))
            except Exception as e:
                raise Exception(f'unable to compute template source path mapping for "{spec_dst}" - {e}')
            if not spec_full_srcs:
                raise Exception(f'unable to compute template source path mapping for "{spec_dst}" - "dst" does not resolve to any valid source paths')
            spec_rel_srcs = [os.path.relpath(p, utils.TEMPLATE_DIR) for p in spec_full_srcs]
            for p in spec_full_srcs:
                if not os.path.exists(p):
                    raise Exception(f'unable to compute template source path mapping for "{spec_dst}" - ""')
            spec_rel_dsts = spec_rel_srcs
            spec_full_dsts = [os.path.join(output_dir, p) for p in spec_rel_dsts]
            spec_full_wrks = [os.path.join(working_dir, p) for p in spec_rel_dsts]
            if 'symlink' in spec:
                if len(spec_full_srcs) > 1:
                    raise Exception('unable to compute template symlink path mapping for "{spec_dst}" - "symlink" cannot be specified if "dst" contains expansion expressions')
                spec_full_lnk = utils.get_path(spec['symlink'], output_dir)
                spec_rel_lnk = os.path.relpath(spec_full_lnk, output_dir)
            else:
                spec_full_lnk = ''
                spec_rel_lnk = ''
            for (full_dst, full_src, full_wrk, rel_dst, rel_src) in zip(spec_full_dsts, spec_full_srcs, spec_full_wrks, spec_rel_dsts, spec_rel_srcs):
                mapping.append({
                    'chmod':     spec['chmod'] if 'chmod' in spec else '',
                    'chown':     spec['chown'] if 'chown' in spec else '',
                    'dst_key':   spec_dst,
                    'full_dst':  full_dst,
                    'full_lnk':  spec_full_lnk,
                    'full_src':  full_src,
                    'full_wrk':  full_wrk,
                    'rel_dst':   rel_dst,
                    'rel_lnk':   spec_rel_lnk,
                    'rel_src':   rel_src,
                    'translate': spec['translate'] if 'translate' in spec else True
                })
    logging.debug('----- Path Mappings -----')
    for line in yaml.dump(mapping).splitlines():
        logging.debug(line)
    logging.debug('-------------------------')
    return mapping


def get_lib_paths(conf: dict) -> list[str]:
    '''
    Obtains the list of rendered library extension paths defined in the
    specified template configuration dictionary.
    '''
    if not 'lib' in conf: return []
    flatten = lambda L: [item for sublist in L for item in sublist]
    path_dir = os.path.dirname(conf['template_configuration_file'])
    logging.debug('Parsing library extension paths...')
    try:
        flat_lib = flatten(utils.parse_file_paths(utils.get_path(p, path_dir)) for p in conf['lib'])
    except Exception as e:
        raise Exception(f'unable to parse library extension paths - {e}')
    return flat_lib


def parse(path: str) -> dict:
    '''
    Recursively parses a template configuration file, iteratively merging all
    YAML data.
    '''
    if not os.path.isfile(path):
        raise Exception(f'template configuration file "{path}" does not exist')
    logging.debug(f'Reading template configuration file "{path}"...')
    try:
        with open(path, 'r') as f:
            conf_raw = f.read()
    except Exception as e:
        raise Exception(f'unable to open template configuration file "{path}" - {e}')
    logging.debug(f'Parsing template configuration file "{path}"...')
    try:
        data = yaml.safe_load(conf_raw)
    except Exception as e:
        raise Exception(f'unable to parse template configuration file "{path}" - {e}')
    if not isinstance(data, dict):
        raise Exception(f'template configuration file "{path}" does not resolve to a dictionary of specifications')
    if not 'include' in data: return data
    if not isinstance(data['include'], list):
        raise Exception(f'template configuration file "{path}" include specification is not a list of path specifications')
    logging.debug(f'Handling template configuration file "{path}" includes...')
    flatten = lambda L: [item for sublist in L for item in sublist]
    path_dir = os.path.dirname(path)
    try:
        flat_includes = flatten(
            utils.parse_file_paths(utils.get_path(p, path_dir)) for p in data['include']
        )
    except Exception as e:
        raise Exception(f'template configuration file "{path}" include specification parsing error - {e}')
    for i in flat_includes:
        if not isinstance(i, str):
            raise Exception(f'template configuration file "{path}" include specification is not a list of path specifications')
        idata = parse(i)
        try:
            data = utils.merge_yaml_data(data, idata)
        except Exception as e:
            raise Exception(f'unable to merge data from template configuration file "{path}" include path "{i}" - {e}')
    data['template_configuration_file'] = os.path.realpath(path)
    return data


def validate(conf: dict):
    logging.debug('Validating template configuration file(s) data...')
    if 'files' in conf:
        if not isinstance(conf['files'], list):
            raise Exception('"files" key is not a list of specification dictionaries')
        if any(not isinstance(t, dict) for t in conf['files']):
            raise Exception('"files" key is not a list of specification dictionaries')
        if any(not 'dst' in t for t in conf['files']):
            raise Exception('one or more "files" specifications do not specify the "dst" key')
    if 'lib' in conf:
        if not isinstance(conf['lib'], list):
            raise Exception('"lib" key is not a list of file path specifications')
        if any(not isinstance(l, str) for l in conf['lib']):
            raise Exception('"lib" key is not a list of file path specifications')
