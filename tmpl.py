#!/usr/bin/env python3
'''
tmpl

A generic templating utility.
'''

# ------- Python Library Imports -------

# Standard Library
import argparse
import glob
import importlib.util
import inspect
import logging
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys

# Additional Dependencies
try:
    import jinja2
except ImportError as e:
    sys.exit('Unable to import Jinja2 library - ' + str(e) + '.')
try:
    import yaml
except ImportError as e:
    sys.exit('Unable to import PyYAML library - ' + str(e) + '.')

# --------------------------------------



# ----------- Initialization -----------

HELP_DESCRIPTION = """
A highly-configurable general-purpose templating program.
"""

HELP_EPILOG = """
"""

# Color Sequences
C_BLUE   = '\033[94m'
C_GREEN  = '\033[92m'
C_ORANGE = '\033[93m'
C_RED    = '\033[91m'
C_END    = '\033[0m'
C_BOLD   = '\033[1m'

# Regular Expressions
LIST_REGEX = re.compile(
    r'^[/\w\.\-\ ]*(?P<expr>\[(?P<inner>[/\w\.\-\ ,]+)\])[/\w\.\-\ ]*$'
)
RANGE_REGEX = re.compile(
    r'^[/\w\.\-\ ]*(?P<expr>\[(?P<lower>\d+)\-(?P<upper>\d+)\])[/\w\.\-\ ]*$'
)

# --------------------------------------



# ---------- Private Functions ---------

def _c(instring, color=C_BLUE):
    '''
    Colorizes the specified string.
    '''
    if args.color_output and not color is None:
        return color + instring + C_END
    else:
        return instring


def _get_path(template_path, base_path=''):
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
            return os.path.normpath(os.path.join(template_dir, template_path))


def _merge_yaml_data(data1, data2):
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
                return_dict[key] = _merge_yaml_data(return_dict[key], val)
            else:
                return_dict[key] = val
        return return_dict
    return data2


def _parse_arguments():
    '''
    Parses the command-line arguments into a global dictionary called "args".
    '''
    # Do some pre-parsing for some of the environment variables to prevent crashes
    if not os.getenv('TMPL_LOG_LEVEL', 'info') in ['info', 'debug']:
        sys.exit('Invalid value set for environment variable "TMPL_LOG_LEVEL".')
    if not os.getenv('TMPL_LOG_MODE', 'append') in ['append', 'overwrite']:
        sys.exit('Invalid value set for environment variable "TMPL_LOG_MODE".')
    argparser = argparse.ArgumentParser(
        description = HELP_DESCRIPTION,
        epilog = HELP_EPILOG,
        usage = 'tmpl TEMPLATE_CONF [-o DEST] [...]',
        add_help = False,
        formatter_class = lambda prog: argparse.RawDescriptionHelpFormatter(prog, max_help_position=45, width=100)
    )
    argparser.add_argument(
        'template_conf',
        help = 'Specifies the path to the template configuration YAML file.',
    )
    argparser.add_argument(
        '-b',
        '--base-dir',
        default = os.getenv('TMPL_BASE_DIR', ''),
        dest = 'base_dir',
        help = '[env: TMPL_BASE_DIR] Specifies the base directory from which template files will be loaded. Defaults to the directory containing the specified template configuration file.',
        metavar = 'DIR'
    )
    argparser.add_argument(
        '--block-end-string',
        default = os.getenv('TMPL_BLOCK_END_STR', '%}'),
        dest = 'block_end_string',
        help = '[env: TMPL_BLOCK_END_STR] Specifies the string marking the end of a Jinja template block. Defaults to "%%}".',
        metavar = 'STR'
    )
    argparser.add_argument(
        '--block-start-string',
        default = os.getenv('TMPL_BLOCK_START_STR', '{%'),
        dest = 'block_start_string',
        help = '[env: TMPL_BLOCK_START_STR] Specifies the string marking the start of a Jinja template block. Defaults to "{%%".',
        metavar = 'STR'
    )
    argparser.add_argument(
        '--comment-end-string',
        default = os.getenv('TMPL_COMMENT_END_STR', '#}'),
        dest = 'comment_end_string',
        help = '[env: TMPL_COMMENT_END_STR] Specifies the string marking the end of a Jinja template comment. Defaults to "#}".',
        metavar = 'STR'
    )
    argparser.add_argument(
        '--comment-start-string',
        default = os.getenv('TMPL_COMMENT_START_STR', '{#'),
        dest = 'comment_start_string',
        help = '[env: TMPL_COMMENT_START_STR] Specifies the string marking the start of a Jinja template comment. Defaults to "{#".',
        metavar = 'STR'
    )
    argparser.add_argument(
        '--delete',
        action = 'store_true',
        dest = 'delete',
        help = 'Specifies that the script should delete any files in the output directory that are not part of the generated files. Certain files and subdirectories may be preserved with the "--exclude" option.'
    )
    argparser.add_argument(
        '--dont-trim-blocks',
        action = 'store_false',
        dest = 'trim_jinja_blocks',
        help = 'Specifies that the first newline character after a Jinja block should NOT be removed.'
    )
    argparser.add_argument(
        '-d',
        '--dry-run',
        action = 'store_true',
        dest = 'dry_run',
        help = 'Specifies that the script should only execute a dry-run, preventing the generated files from being copied from the working directory to the output directory.'
    )
    argparser.add_argument(
        '--exclude',
        default = os.getenv('TMPL_EXCLUDE', '').split(' '),
        dest = 'exclude',
        help = '[env: TMPL_EXCLUDE] Specifies an additional list of files or directories relative to the specified output directory that should be preserved on write (if "--delete" is supplied).',
        metavar = 'PATH',
        nargs = '+'
    )
    argparser.add_argument(
        '-h',
        '--help',
        action = 'help',
        help = 'Displays help and usage information.'
    )
    argparser.add_argument(
        '-f',
        '--log-file',
        default = os.getenv('TMPL_LOG_FILE', ''),
        dest = 'log_file',
        help = '[env: TMPL_LOG_FILE] Specifies a log file to write to in addition to stdout/stderr.',
        metavar = 'FILE'
    )
    argparser.add_argument(
        '-l',
        '--log-level',
        choices = ['info', 'debug'],
        default = os.getenv('TMPL_LOG_LEVEL', 'info'),
        dest = 'log_level',
        help = '[env: TMPLE_LOG_LEVEL] Specifies the log level of the script, being either "info" or "debug". Defaults to "info". This option is ignored if "--log-file" is not specified.',
        metavar = 'LVL'
    )
    argparser.add_argument(
        '-m',
        '--log-mode',
        choices = ['append', 'overwrite'],
        default = os.getenv('TMPL_LOG_MODE', 'append'),
        dest = 'log_mode',
        help = '[env: TMPL_LOG_MODE] Specifies whether to "append" or "overwrite" the specified log file. Defaults to "append". This option is ignored if "--log-file" is not specified.',
        metavar = 'MODE'
    )
    argparser.add_argument(
        '--no-color',
        action = 'store_false',
        dest = 'color_output',
        help = 'Disables color output to stdout/stderr.'
    )
    argparser.add_argument(
        '-o',
        '--output',
        default = os.path.expanduser(os.getenv('TMPL_OUTPUT', os.getcwd())),
        dest = 'output',
        help = '[env: TMPL_OUTPUT] Specifies the output directory of the generated files. Defaults to the current working directory.',
        metavar = 'DIR'
    )
    argparser.add_argument(
        '--rsync-executable',
        default = os.getenv('TMPL_RSYNC_PATH', '/usr/bin/rsync'),
        dest = 'rsync_executable',
        help = '[env: TMPL_RSYNC_PATH] Specifies a file path to the rsync executable utilized for transferring directories. Defaults to "/usr/bin/rsync".',
        metavar = 'FILE'
    )
    argparser.add_argument(
        '--stdin',
        action = 'store_true',
        dest = 'stdin',
        help = 'Specifies that the script should read raw Jinja-templated content from STDIN instead of utilizing the "files" key in the specified template configuration file.'
    )
    argparser.add_argument(
        '--variable-end-string',
        default = os.getenv('TMPL_VAR_END_STR', '}}'),
        dest = 'variable_end_string',
        help = '[env: TMPL_VAR_END_STR] Specifies the string marking the end of a Jinja template variable. Defaults to "}}".',
        metavar = 'STR'
    )
    argparser.add_argument(
        '--variable-start-string',
        default = os.getenv('TMPL_VAR_START_STR', '{{'),
        dest = 'variable_start_string',
        help = '[env: TMPL_VAR_START_STR] Specifies the string marking the start of a Jinja template variable. Defaults to "{{".',
        metavar = 'STR'
    )
    argparser.add_argument(
        '-w',
        '--working-directory',
        default = os.getenv('TMPL_WORKING_DIR', '/tmp/tmpl'),
        dest = 'working_directory',
        help = '[env: TMPL_WORKING_DIR] Specifies the working directory. Defaults to "/tmp/tmpl".',
        metavar = 'DIR'
    )
    global args
    args = argparser.parse_args()


def _parse_file_paths(path_spec):
    '''
    Returns the equivalent list of file paths given a path specification.
    With the expection of globbing, the resulting paths are only computed and
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
            raise Exception('path specification globbing encountered an exception - ' + str(e))
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
            
    
def _rsync(src, dst, rsync_args=''):
    '''
    Performs an rsync from the specified source path to the specified
    destination path.
    '''
    if args.dry_run:
        true_rsync_args = rsync_args + ' --dry-run'
    else:
        true_rsync_args = rsync_args
    cmd = '{rsync_exec} {args} {src} {dst}'.format(
        rsync_exec = args.rsync_executable,
        args = true_rsync_args,
        src = src,
        dst = dst
    )
    return _run_process(cmd)


def _run_process(cmd, splitlines=True):
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


def _setup_logging():
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


def _step(instring, color=C_BLUE):
    '''
    Formats the specified string as a "step".
    '''
    return _c('::', color) + ' ' + _c(instring, C_BOLD)


def _substep(instring, color=C_BLUE):
    '''
    Formats the specified string as a "sub-step".
    '''
    return '  ' + _c('-->', color) + ' ' + instring


def _subsubstep(instring, color=None):
    '''
    Formats the specified string as a "sub-sub-step".
    '''
    return '      ' + _c(instring, color)


def _tmpl_domain_join(*variables):
    '''
    A Jinja function that acts like os.path.join but with domain strings.
    '''
    return '.'.join([x.strip('.') for x in variables])


def _tmpl_env(name, default=None):
    '''
    A Jinja function that literally just calls os.getenv() under the hood.
    '''
    return os.getenv(name, default)


def _tmpl_file_ext(path):
    '''
    A Jinja function that returns the file extension of the specified path.
    '''
    basename = os.path.basename(path)
    if not '.' in basename:
        return ''
    else:
        return basename.split('.', 1)[1]


def _tmpl_file_name(path):
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
def _tmpl_get(context, variable):
    '''
    A Jinja function that returns the value of the specified variable string name.
    '''
    return context.resolve(variable)


def _tmpl_get_host(ip):
    '''
    A Jinja function that returns the host of a particular IP.
    '''
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception as e:
        raise Exception("get_host('" + ip + "') - Unable to obtain host for specified IP address - " + str(e) + '.')

    
def _tmpl_get_ip(host):
    '''
    A Jinja function that returns the IP of a particular host.
    '''
    try:
        return socket.gethostbyname(host)
    except Exception as e:
        raise Exception("get_ip('" + host + "') - Unable to obtain IP address for specified host - " + str(e) + '.')

    
def _tmpl_get_output(cmd):
    '''
    A Jinja function that returns the output of the specified command.
    '''
    try:
        return _run_process(cmd, splitlines=False)[1]
    except Exception as e:
        raise Exception('Unable to get output from command "' + cmd + '" - ' + str(e) + '.')


def _tmpl_parse_yaml(yaml_str):
    '''
    A Jinja function that parses the specified YAML string.
    '''
    try:
        return yaml.safe_load(yaml_str)
    except Exception as e:
        raise Exception('Unable to parse YAML string - ' + str(e))


def _tmpl_print(message):
    '''
    A Jinja function that prints and logs the specified message.
    '''
    if not args.stdin:
        print(_subsubstep(str(message), C_BLUE))
    logging.info(str(message))
    return ''


def _tmpl_raise(message):
    '''
    A Jinja function that raises an exception with the supplied message.
    '''
    raise Exception(message)


def _tmpl_read_file(path):
    '''
    Returns the contents of the file located at the specified path, relative to
    the path to the template configuration file.
    '''
    actual_path = _get_path(path)
    if not os.path.isfile(actual_path):
        raise Exception('Cannot read file "' + actual_path + '" - specified file path does not exist.')
    try:
        with open(actual_path, 'r') as f:
            contents = f.read()
    except Exception as e:
        raise Exception('Cannot read file "' + actual_path + '" - ' + str(e))
    return contents


@jinja2.contextfunction
def _tmpl_require(context, *variables):
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
                raise Exception('Required variable "' + splitvar[0] + '" not found in within the context of "' + context.name + '".')
            if not splitvar[1] in context[splitvar[0]]:
                raise Exception('Required variable "' + variable + '" not found in within the context of "' + context.name + '".')
        else:
            if not variable in context:
                raise Exception('Required variable "' + variable + '" not found in within the context of "' + context.name + '".')
    return ''

# --------------------------------------



# ---------- Public Functions ----------

def compute_mapping():
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
    EC = 6
    message(_substep('Computing path mapping...'))
    logging.debug('Computing path mapping...')
    global templates_maps
    templates_maps = []
    for spec in conf['files']:
        logging.debug('Computing template path mapping for "' + spec['dst'] + '"...')
        if 'src' in spec:
            logging.debug('SRC: ' + spec['src'])
            try:
                spec_full_srcs = _parse_file_paths(_get_path(spec['src']))
            except Exception as e:
                emessage(_subsubstep('Unable to compute template source path mapping - ' + str(e) + '.', C_RED))
                logging.critical('Unable to compute template source path mapping - ' + str(e) + '.')
                sys.exit(EC)
            if not spec_full_srcs:
                emessage(_subsubstep('Unable to compute template source path mapping - "src" does not resolve to any valid source paths.', C_RED))
                logging.critical('Unable to compute template source path mapping - "src" does not resolve to any valid source paths.')
                sys.exit(EC)
            logging.debug('FULL SOURCE PATHS: ' + str(spec_full_srcs))
            spec_rel_srcs = [os.path.relpath(p, template_dir) for p in spec_full_srcs]
            logging.debug('RELATIVE SOURCE PATHS: ' + str(spec_rel_srcs))
            for p in spec_full_srcs:
                if not os.path.exists(p):
                    emessage(_subsubstep('Unable to compute template source path mapping - "' + p + '" does not correspond to a path to an existing file.', C_RED))
                    logging.critical('Unable to compute template source path mapping - "' + p + '" does not correspond to a path to an existing file.')
                    sys.exit(EC)
            logging.debug('DST: ' + spec['dst'])
            try:
                spec_full_dsts = _parse_file_paths(_get_path(spec['dst'], args.output))
            except Exception as e:
                emessage(_subsubstep('Unable to compute template destination path mapping - ' + str(e) + '.', C_RED))
                logging.critical('Unable to compute template destination path mapping - ' + str(e) + '.')
                sys.exit(EC)
            if not spec_full_dsts:
                emessage(_subsubstep('Unable to compute template destination path mapping - "dst" does not resolve to any valid destination paths.', C_RED))
                logging.critical('Unable to compute template destination path mapping - "dst" does not resolve to any valid destination paths.')
                sys.exit(EC)
            if len(spec_full_dsts) > 1:
                emessage(_subsubstep('Unable to compute template destination path mapping - "dst" cannot contain expansion expressions if "src" is specified.', C_RED))
                logging.critical('Unable to compute template destination path mapping - "dst" cannot contain expansion expressions if "src" is specified.')
                sys.exit(EC)
            spec_full_dst = spec_full_dsts[0]
            logging.debug('FULL (OUTPUT) DESTINATION PATH: ' + spec_full_dst)
            spec_rel_dst = os.path.relpath(spec_full_dst, args.output)
            logging.debug('RELATIVE DESTINATION PATH: ' + spec_rel_dst)
            spec_full_wrk = os.path.join(args.working_directory, spec_rel_dst)
            logging.debug('FULL (WORKING) DESTINATION PATH: ' + spec_full_wrk)
            if 'symlink' in spec:
                if len(spec_full_srcs) > 1:
                    emessage(_subsubstep('Unable to compute template symlink path mapping - "symlink" cannot be specified if "src" contains expression expansions.', C_RED))
                    logging.critical('Unable to compute template symlink path mapping - "symlink" cannot be specified if "src" contains expression expansions.')
                    sys.exit(EC)
                spec_full_lnk = _get_path(spec['symlink'], args.output)
                spec_rel_lnk = os.path.relpath(spec_full_lnk, args.output)
            else:
                spec_full_lnk = ''
                spec_rel_lnk = ''
            for (full_src, rel_src) in zip(spec_full_srcs, spec_rel_srcs):
                templates_maps.append({
                    "chmod":     spec['chmod'] if 'chmod' in spec else '',
                    "chown":     spec['chown'] if 'chown' in spec else '',
                    "dst_key":   spec['dst'],
                    "full_dst":  spec_full_dst,
                    "full_lnk":  spec_full_lnk,
                    "full_src":  full_src,
                    "full_wrk":  spec_full_wrk,
                    "rel_dst":   spec_rel_dst,
                    "rel_lnk":   spec_rel_lnk,
                    "rel_src":   rel_src,
                    "translate": spec['translate'] if 'translate' in spec else True
                })
        else:
            logging.debug('SRC: ' + spec['dst'] + ' (from "dst")')
            try:
                spec_full_srcs = _parse_file_paths(_get_path(spec['dst']))
            except Exception as e:
                emessage(_subsubstep('Unable to compute template source path mapping - ' + str(e) + '.', C_RED))
                logging.critical('Unable to compute template source path mapping - ' + str(e) + '.')
                sys.exit(EC)
            if not spec_full_srcs:
                emessage(_subsubstep('Unable to compute template source path mapping - "dst" does not resolve to any valid source paths.', C_RED))
                logging.critical('Unable to compute template source path mapping - "dst" does not resolve to any valid source paths.')
                sys.exit(EC)
            logging.debug('FULL SOURCE PATHS: ' + str(spec_full_srcs))
            spec_rel_srcs = [os.path.relpath(p, template_dir) for p in spec_full_srcs]
            logging.debug('RELATIVE SOURCE PATHS: ' + str(spec_rel_srcs))
            for p in spec_full_srcs:
                if not os.path.exists(p):
                    emessage(_subsubstep('Unable to compute template source path mapping - "' + p + '" does not correspond to a path to an existing file.', C_RED))
                    logging.critical('Unable to compute template source path mapping - "' + p + '" does not correspond to a path to an existing file.')
                    sys.exit(EC)
            spec_rel_dsts  = spec_rel_srcs
            logging.debug('RELATIVE DESTINATION PATHS: ' + str(spec_rel_dsts))
            spec_full_dsts = [os.path.join(args.output, p) for p in spec_rel_dsts]
            logging.debug('FULL (OUTPUT) DESINATION PATHS: ' + str(spec_full_dsts))
            spec_full_wrks = [os.path.join(args.working_directory, p) for p in spec_rel_dsts]
            logging.debug('FULL (WORKING) DESTINATION PATHS: ' + str(spec_full_wrks))
            if 'symlink' in spec:
                if len(spec_full_srcs) > 1:
                    emessage(_subsubstep('Unable to compute template symlink path mapping - "symlink" cannot be specified if "dst" contains expression expansions.', C_RED))
                    logging.critical('Unable to compute template symlink path mapping - "symlink" cannot be specified if "dst" contains expression expansions.')
                    sys.exit(EC)
                spec_full_lnk = _get_path(spec['symlink'], args.output)
                spec_rel_lnk = os.path.relpath(spec_full_lnk, args.output)
            else:
                spec_full_lnk = ''
                spec_rel_lnk = ''
            for (full_dst, full_src, full_wrk, rel_dst, rel_src) in zip(spec_full_dsts, spec_full_srcs, spec_full_wrks, spec_rel_dsts, spec_rel_srcs):
                templates_maps.append({
                    "chmod":     spec['chmod'] if 'chmod' in spec else '',
                    "chown":     spec['chown'] if 'chown' in spec else '',
                    "dst_key":   spec['dst'],
                    "full_dst":  full_dst,
                    "full_lnk":  spec_full_lnk,
                    "full_src":  full_src,
                    "full_wrk":  full_wrk,
                    "rel_dst":   rel_dst,
                    "rel_lnk":   spec_rel_lnk,
                    "rel_src":   rel_src,
                    "translate": spec['translate'] if 'translate' in spec else True
                })
    logging.debug('TEMPLATE MAPPING: ' + str(templates_maps))
    

def emessage(instring):
    '''
    Prints the specified string to stderr.
    This function will not print anything if STDIN of the script isn't a tty.
    '''
    if not args.stdin: sys.stderr.write(instring + '\n')


def get_hostname():
    '''
    Obtains the hostname of the machine.
    '''
    logging.debug('Getting hostname and FQDN...')
    try:
        global hostname
        hostname = socket.gethostname().split('.', 1)[0]
        global fqdn
        fqdn = socket.getfqdn()
    except Exception as e:
        logging.critical('Unable to discern hostname - ' + str(e) + '.')
        sys.exit(1)
    logging.debug('Hostname: ' + hostname)
    logging.debug('FQDN: ' + fqdn)


def main():
    '''
    The entrypoint of the script.
    '''
    # (2) Parse command-line arguments
    _parse_arguments()
    
    # (1) Setup logging
    _setup_logging()

    # Log CLI arguments at the DEBUG level
    logging.debug('----- CLI Arguments -----')
    dargs = vars(args)
    for a in dargs:
        logging.debug(a + ' : ' + str(dargs[a]))
    logging.debug('-------------------------')

    # (1) Get the hostname of the machine
    get_hostname()

    logging.info('Starting process...')
    
    # (2) Set-up and validate the environment
    validate_environment()
    
    # (3) Parse template configuration file
    parse_config()

    # (4) Validate the template configuration file
    validate_config()

    # (5) Set-up the jinja environment
    setup_jinja()

    if not args.stdin:
        # (6) Compute file path mappings
        compute_mapping()
    
        # (7) Translate templates (saving into the working directory)
        translate_templates()
    
        # (8) Write to the output directory (and generate symlinks)
        write_output()
    else:
        # (9) Handle piped STDIN
        translate_stdin()
    
    logging.info('Process complete.')

    # We are done.
    sys.exit(0)

    
def message(instring):
    '''
    Prints the specified string to stdout.
    This function will not print anything if STDIN of the script isn't a tty.
    '''
    if not args.stdin: print(instring)


def parse_config():
    '''
    Parses the template configuration YAML file into a global dictionary object.
    '''
    EC = 3
    message(_step('Loading template configuration file...'))
    logging.info('Loading template configuration file...')
    message(_substep('Reading template configuration file...'))
    logging.debug('Reading template configuration file...')
    try:
        with open(args.template_conf, 'r') as yamlf:
            conf_raw = yamlf.read()
    except Exception as e:
        emessage(_subsubstep('Unable to read template configuration file - ' + str(e) + '.', C_RED))
        logging.critical('Unable to read template configuration file - ' + str(e) + '.')
        sys.exit(EC)
    message(_substep('Parsing template configuration file...'))
    logging.debug('Parsing template configuration file...')
    try:
        global conf
        conf = yaml.safe_load(conf_raw)
    except Exception as e:
        emessage(_subsubstep('Unable to parse template configuration file - ' + str(e) + '.', C_RED))
        logging.critical('Unable to parse template configuration file - ' + str(e) + '.')
        sys.exit(EC)
    if 'include' in conf:
        message(_substep('Parsing template configuration file includes...'))
        logging.debug('Parsing template configuration file includes...')
        if not isinstance(conf['include'], list):
            emessage(_subsubstep('Unable to parse template configuration file includes - "include" specification is not a list of file paths.', C_RED))
            logging.critical('Unable to parse template configuration file includes - "include" specification is not a list of file paths.')
            sys.exit(EC)
        flatten = lambda L: [item for sublist in L for item in sublist]
        try:
            flat_includes = flatten([_parse_file_paths(_get_path(p, os.path.dirname(args.template_conf))) for p in conf['include']])
        except Exception as flat_e:
            emessage(_subsubstep('Unable to parse template configuration file includes - "include" specification parsing error - ' + str(flat_e) + '.', C_RED))
            logging.critical('Unable to parse template configuration file includes - "include" specification parsing error - ' + str(flat_e) + '.')
            sys.exit(EC)
        for i in flat_includes:
            if not isinstance(i, str):
                emessage(_subsubstep('Unable to parse template configuration file includes - "include" specification is not a list of file paths.', C_RED))
                logging.critical('Unable to parse template configuration file includes - "include" specification is not a list of file paths.')
                sys.exit(EC)
            logging.debug('Validating template configuration file include "' + i + '"...')
            if not os.path.isfile(i):
                emessage(_subsubstep('Unable to validate template configuration file include "' + i + '" - value is not a path to an existing file.', C_RED))
                logging.critical('Unable to validate template configuration file include "' + i + '" - value is not a path to an existing file.')
                sys.exit(EC)
            logging.debug('Loading template configuration file include "' + i + '"...')
            try:
                with open(i, 'r') as ifile:
                    icontents = ifile.read()
            except Exception as e:
                emessage(_subsubstep('Unable to load template configuration file include "' + i + '" - ' + str(e) + '.', C_RED))
                logging.critical('Unable to load template configuration file include "' + i + '" - ' + str(e) + '.')
                sys.exit(EC)
            logging.debug('Parsing template configuration file include "' + i + '"...')
            try:
                iconf = yaml.safe_load(icontents)
            except Exception as e:
                emessage(_subsubstep('Unable to parse template configuration file include "' + i + '" - ' + str(e) + '.', C_RED))
                logging.critical('Unable to parse template configuration file include "' + i + '" - ' + str(e) + '.')
                sys.exit(EC)
            logging.debug('Merging template configuration file include "' + i + '"...')
            try:
                conf = _merge_yaml_data(conf, iconf)
            except Exception as e:
                emessage(_subsubstep('Unable to merge template configuration file include "' + i + '" - ' + str(e) + '.', C_RED))
                logging.critical('Unable to merge template configuration file include "' + i + '" - ' + str(e) + '.')
                sys.exit(EC)
    logging.debug('----- Template Configuration -----')
    for x in conf:
        logging.debug(x + ' : ' + str(conf[x]))
    logging.debug('----------------------------------')


def setup_jinja():
    '''
    Sets-up the Jinja environment for template parsing.
    '''
    EC = 5
    message(_step('Setting-up templating environment...'))
    logging.info('Setting-up templating environment...')
    message(_substep('Initializing loader...'))
    logging.debug('Initializing loader...')
    try:
        fsloader = jinja2.FileSystemLoader(template_dir)
    except Exception as e:
        emessage(_subsubstep('Unable to initialize templating loader - ' + str(e) + '.', C_RED))
        logging.critical('Unable to initialize templating loader - ' + str(e) + '.')
        sys.exit(EC)
    message(_substep('Initializing environment...'))
    logging.debug('Initializing environment...')
    try:
        global jinja_env
        jinja_env = jinja2.Environment(
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
    except Exception as e:
        emessage(_subsubstep('Unable to initialize templating environment - ' + str(e) + '.', C_RED))
        logging.critical('Unable to initialize templating environment - ' + str(e) + '.')
        sys.exit(EC)
    message(_substep('Initializing extensions...'))
    logging.debug('Initializing extensions...')
    try:
        # Provided Variables
        jinja_env.globals['fqdn']                        = fqdn
        jinja_env.globals['hostname']                    = hostname
        jinja_env.globals['output_directory']            = os.path.realpath(args.output)
        jinja_env.globals['template_configuration_file'] = os.path.realpath(args.template_conf)

        # Custom Functions
        jinja_env.globals['domain_join']   = _tmpl_domain_join
        jinja_env.globals['env']           = _tmpl_env
        jinja_env.globals['file_ext']      = _tmpl_file_ext
        jinja_env.globals['file_name']     = _tmpl_file_name
        jinja_env.globals['get']           = _tmpl_get
        jinja_env.globals['get_host']      = _tmpl_get_host
        jinja_env.globals['get_ip']        = _tmpl_get_ip
        jinja_env.globals['get_output']    = _tmpl_get_output
        jinja_env.globals['parse_yaml']    = _tmpl_parse_yaml
        jinja_env.globals['path_basename'] = os.path.basename
        jinja_env.globals['path_dirname']  = os.path.dirname
        jinja_env.globals['path_join']     = os.path.join
        jinja_env.globals['print']         = _tmpl_print
        jinja_env.globals['raise']         = _tmpl_raise
        jinja_env.globals['read_file']     = _tmpl_read_file
        jinja_env.globals['require']       = _tmpl_require
    except Exception as e:
        emessage(_subsubstep('Unable to initialize templating extensions - ' + str(e) + '.', C_RED))
        logging.critical('Unable to initialize templating extensions - ' + str(e) + '.')
        sys.exit(EC)
    if 'lib' in conf:
        message(_substep('Initializing libraries...'))
        logging.debug('Initializing libraries...')
        flatten = lambda L: [item for sublist in L for item in sublist]
        try:
            flat_lib = flatten([_parse_file_paths(_get_path(p, os.path.dirname(args.template_conf))) for p in conf['lib']])
        except Exception as e:
            emessage(_subsubstep('Unable to parse library extension paths - ' + str(e) + '.', C_RED))
            logging.critical('Unable to parse library extension paths - ' + str(e) + '.')
            sys.exit(EC)
        for libpath in flat_lib:
            logging.debug('Loading library "' + libpath + '"...')
            try:
                spec = importlib.util.spec_from_file_location(os.path.basename(libpath).split('.', 1)[0], libpath)
            except Exception as e:
                emessage(_subsubstep('Unable to obtain spec for library file "' + libpath + '" - ' + str(e) + '.', C_RED))
                logging.critical('Unable to obtain spec library file "' + libpath + '" - ' + str(e) + '.')
                sys.exit(EC)
            try:
                mod = importlib.util.module_from_spec(spec)
            except Exception as e:
                emessage(_subsubstep('Unable to load module from library file "' + libpath + '" - ' + str(e) + '.', C_RED))
                logging.critical('Unable to load module from library file "' + libpath + '" - ' + str(e) + '.')
                sys.exit(EC)
            try:
                spec.loader.exec_module(mod)
            except Exception as e:
                emessage(_subsubstep('Unable to execute module from library file "' + libpath + '" - ' + str(e) + '.', C_RED))
                logging.critical('Unable to execute module from library file "' + libpath + '" - ' + str(e) + '.')
                sys.exit(EC)
            mod_functions = inspect.getmembers(mod, inspect.isfunction)
            if not mod_functions:
                emessage(_subsubstep('Warning: Library file "' + libpath + '" contains no defined functions.', C_RED))
                logging.warning('Library file "' + libpath + '" contains no defined functions.')
            else:
                logging.debug('MODULE FUNCTIONS : ' + str([i[0] for i in mod_functions]))
                for f in mod_functions:
                    jinja_env.globals[f[0]] = f[1]

            
def translate_stdin():
    '''
    Translates Jinja statements handed to STDIN to STDOUT.
    '''
    EC = 9
    logging.info('Translating standard input...')
    logging.debug('Reading standard input...')
    try:
        stdin = sys.stdin.read()
    except Exception as e:
        logging.critical('Unable to read standard input - ' + str(e) + '.')
        sys.exit(EC)
    logging.debug('Loading template...')
    try:
        template = jinja_env.from_string(stdin)
    except Exception as e:
        logging.critical('Unable to load template - ' + str(e) + '.')
        sys.exit(EC)
    logging.debug('Rendering template...')
    try:
        rendered = template.render(**conf)
    except jinja2.TemplateSyntaxError as e:
        logging.critical('Unable to render template - syntax error on line ' + str(e.lineno) + ' - ' + str(e))
        sys.exit(EC)
    except Exception as e:
        logging.critical('Unable to render template - ' + str(e) + '.')
        sys.exit(EC)
    logging.debug('Writing to standard output...')
    try:
        sys.stdout.write(rendered + '\n')
    except Exception as e:
        logging.critical('Unable to write to standard output - ' + str(e) + '.')
        sys.exit(EC)


def translate_templates():
    '''
    Translates the source templates into their final forms within the working
    directory.
    '''
    EC = 7
    message(_step('Translating templates...'))
    logging.info('Translating templates...')
    for m in templates_maps:
        message(_substep(m['rel_dst']))
        if m['translate']:
            logging.info('Translating "' + m['full_src'] + '" into "' + m['full_wrk'] + '"...')
            logging.debug('Loading template...')
            try:
                template = jinja_env.get_template(m['rel_src'])
            except jinja2.TemplateSyntaxError as e:
                emessage(_subsubstep('Unable to load template - syntax error on line ' + str(e.lineno) + ' - ' + str(e), C_RED))
                logging.critical('Unable to load template - syntax error on line ' + str(e.lineno) + ' - ' + str(e))
                sys.exit(EC)
            except Exception as e:
                emessage(_subsubstep('Unable to load template - ' + str(e) + '.', C_RED))
                logging.critical('Unable to load template - ' + str(e) + '.')
                sys.exit(EC)
            logging.debug('Augmenting template configuration...')
            aug = conf.copy()
            aug['file'] = os.path.basename(m['rel_dst'])
            aug['this'] = next(t for t in conf['files'] if t['dst'] == m['dst_key'])
            logging.debug('Rendering template...')
            try:
                rendered = template.render(**aug)
            except jinja2.TemplateSyntaxError as e:
                emessage(_subsubstep('Unable to render template - syntax error on line ' + str(e.lineno) + ' - ' + str(e), C_RED))
                logging.critical('Unable to render template - syntax error on line ' + str(e.lineno) + ' - ' + str(e))
                sys.exit(EC)
            except Exception as e:
                emessage(_subsubstep('Unable to render template - ' + str(e) + '.', C_RED))
                logging.critical('Unable to render template - ' + str(e) + '.')
                sys.exit(EC)
            logging.debug('Writing rendered file to working directory...')
            if not os.path.isdir(os.path.dirname(m['full_wrk'])):
                try:
                    os.makedirs(os.path.dirname(m['full_wrk']))
                except Exception as e:
                    emessage(_subsubstep('Unable to write rendered file to working directory - unable to create parent directory - ' + str(e) + '.', C_RED))
                    logging.critical('Unable to write rendered file to working directory - unable to create parent directory - ' + str(e) + '.')
                    sys.exit(EC)
            try:
                with open(m['full_wrk'], 'w') as f:
                    f.write(rendered)
            except Exception as e:
                emessage(_subsubstep('Unable to write rendered file to working directory - ' + str(e) + '.', C_RED))
                logging.critical('Unable to write rendered file to working directory - ' + str(e) + '.')
                sys.exit(EC)
        else:
            logging.info('Copying "' + m['full_src'] + '" to "' + m['full_wrk'] + '"...')
            if not os.path.isdir(os.path.dirname(m['full_wrk'])):
                try:
                    os.makedirs(os.path.dirname(m['full_wrk']))
                except Exception as e:
                    emessage(_subsubstep('Unable to copy file to working directory - unable to create parent directory - ' + str(e) + '.', C_RED))
                    logging.critical('Unable to copy file to working directory - unable to create parent directory - ' + str(e) + '.')
                    sys.exit(EC)
            try:
                shutil.copyfile(m['full_src'], m['full_wrk'])
            except Exception as e:
                emessage(_subsubstep('Unable to copy file to working directory - ' + str(e) + '.', C_RED))
                logging.critical('Unable to copy file to working directory - ' + str(e) + '.')
                sys.exit(EC)
        
    
def validate_config():
    '''
    Validates the fully-parsed template configuration.
    '''
    EC = 4
    message(_substep('Validating template configuration...'))
    logging.debug('Validating template configuration...')
    if not args.stdin:
        if not 'files' in conf:
            emessage(_subsubstep('Invalid template configuration - "files" specification not found.', C_RED))
            logging.critical('Invalid template configuration - "files" specification not found.')
            sys.exit(EC)
        if not isinstance(conf['files'], list):
            emessage(_subsubstep('Invalid template configuration - "files" specification is not a list of dictionaries.', C_RED))
            logging.critical('Invalid template configuration - "files" specification is not a list of dictionaries.')
            sys.exit(EC)
        if any([not isinstance(t, dict) for t in conf['files']]):
            emessage(_subsubstep('Invalid template configuration - "files" specification is not a list of dictionaries.', C_RED))
            logging.critical('Invalid template configuration - "files" specification is not a list of dictionaries.')
            sys.exit(EC)
        if any([not 'dst' in t for t in conf['files']]):
            emessage(_subsubstep('Invalid template configuration - one or more template definitions do not specify a destination.', C_RED))
            logging.critical('Invalid template configuration - one or more template definitions do not specify a destination.')
            sys.exit(EC)
    if 'lib' in conf:
        if not isinstance(conf['lib'], list):
            emessage(_subsubstep('Invalid template configuration - "lib" specification is not a list of file paths.', C_RED))
            logging.critical('Invalid template configuration - "lib" specification is not a list of file paths.')
            sys.exit(EC)
        if any([not isinstance(l, str) for l in conf['lib']]):
            emessage(_subsubstep('Invalid template configuration - "lib" specification is not a list of file paths.', C_RED))
            logging.critical('Invalid template configuration - "lib" specification is not a list of file paths.')
            sys.exit(EC)

    
def validate_environment():
    '''
    Validates that the executing environment is sufficient to proceed.
    '''
    EC = 2
    message(_step('Validating working environment...'))
    logging.info('Validating working environment...')
    message(_substep('Validating rsync executable path...'))
    logging.debug('Validating rsync executable path...')
    if not os.path.isfile(args.rsync_executable):
        emessage(_subsubstep('Specified rsync executable path does not exist.', C_RED))
        logging.critical('Specified rsync executable path does not exist.')
        sys.exit(EC)
    message(_substep('Validating template base directory...'))
    logging.debug('Validating template base directory...')
    if args.base_dir and not os.path.isdir(args.base_dir):
        emessage(_subsubstep('Specified template base directory does not exist.', C_RED))
        logging.critical('Specified template base directory does not exist.')
        sys.exit(EC)
    message(_substep('Validating template configuration file...'))
    logging.debug('Validating template configuration file...')
    if not os.path.isfile(args.template_conf):
        if not os.path.isdir(args.template_conf):
            emessage(_subsubstep('Specified template configuration path does not exist.', C_RED))
            logging.critical('Specified template configuration path does not exist.')
            sys.exit(EC)
        else:
            logging.debug('Selecting suitable template configuration file within specified directory...')
            files = [x for x in os.listdir(args.template_conf) if os.path.isfile(os.path.join(args.template_conf, x))]
            if not files:
                emessage(_subsubstep('Specified template configuration file directory does not contain any template configuration files.', C_RED))
                logging.critical('Specified template configuration file directory does not contain any template configuration files.')
                sys.exit(EC)
            elif 'tmpl.yaml' in files:
                args.template_conf = os.path.join(args.template_conf, 'tmpl.yaml')
            elif 'tmpl.yml' in files:
                args.template_conf = os.path.join(args.template_conf, 'tmpl.yml')
            elif hostname + '.yaml' in files:
                args.template_conf = os.path.join(args.template_conf, hostname + '.yaml')
            elif hostname + '.yml' in files:
                args.template_conf = os.path.join(args.template_conf, hostname + '.yml')
            else:
                found_match = False
                for f in files:
                    if (f.endswith('.yaml') or f.endswith('.yml')) and f.rsplit('.', 1)[0] in hostname:
                        args.template_conf = os.path.join(args.template_conf, f)
                        found_match = True
                        break
                if not found_match:
                    emessage(_subsubstep('Specified template configuration file directory does not contain any selectable template configuration files.', C_RED))
                    logging.critical('Specified template configuration file directory does not contain any selectable template configuration files.')
                    sys.exit(EC)
            message(_subsubstep('Automatically selected template configuration file "' + args.template_conf + '".', C_BLUE))
            logging.info('Automatically selected template configuration file "' + args.template_conf + '".')
    global template_dir
    if not args.base_dir:
        template_dir = os.path.dirname(args.template_conf)
    else:
        template_dir = args.base_dir
    message(_substep('Validating working directory...'))
    logging.debug('Validating working directory...')
    if os.path.isfile(args.working_directory):
        emessage(_subsubstep('Specified working directory is an existing file.', C_RED))
        logging.critical('Specified working directory is an existing file.')
        sys.exit(EC)
    if os.path.isdir(args.working_directory):
        logging.debug('Working directory already exists. Deleting previous working directory...')
        try:
            shutil.rmtree(args.working_directory)
        except Exception as e:
            emessage(_subsubstep('Unable to delete previous working directory - ' + str(e) + '.', C_RED))
            logging.critical('Unable to delete previous working directory - ' + str(e) + '.')
            sys.exit(EC)
    logging.debug('Creating working directory...')
    try:
        os.makedirs(args.working_directory)
    except Exception as e:
        emessage(_subsubstep('Unable to create working directory - ' + str(e) + '.', C_RED))
        logging.critical('Unable to create working directory - ' + str(e) + '.')
        sys.exit(EC)


def write_output():
    '''
    Transfers the newly generated files from the working directory to the specified output directory.
    '''
    EC = 8
    if args.dry_run:
        message(_step('Finalizing translation process (DRY RUN)...'))
        logging.info('Finalizing translation process (DRY RUN)...')
    else:
        message(_step('Finalizing translation process...'))
        logging.info('Finalizing translation process...')
    if not os.path.isdir(args.output):
        logging.debug('Creating output directory...')
        try:
            if not args.dry_run: os.makedirs(args.output)
        except Exception as e:
            emessage(_subsubstep('Unable to create output directory - ' + str(e) + '.', C_RED))
            logging.critical('Unable to create output directory - ' + str(e) + '.')
            sys.exit(EC)
    message(_substep('Transferring files to output directory...'))
    logging.debug('Transferring files to output directory...')
    rsync_args = '-a -h --progress'
    if args.delete: rsync_args += ' --delete'
    if args.exclude and args.exclude[0]:
        for x in args.exclude:
            rsync_args += ' --exclude ' + x
    logging.debug('RSYNC ARGS: ' + rsync_args)
    try:
        (r_o, r_ec) = _rsync(
            args.working_directory.rstrip('/') + '/',
            args.output.rstrip('/') + '/',
            rsync_args
        )
    except Exception as e:
        emessage(_subsubstep('Unable to transfer files to output directory - ' + str(e) + '.', C_RED))
        logging.critical('Unable to transfer files to output directory - ' + str(e) + '.')
        sys.exit(EC)
    logging.debug('RSYNC EXIT CODE: ' + str(r_ec))
    if r_ec != 0:
        for l in r_o:
            logging.critical('RSYNC OUTPUT: ' + l)
        emessage(_subsubstep('Unable to transfer files to output directory - rsync subprocess returned non-zero exit code.', C_RED))
        logging.critical('Unable to transfer files to output directory - rsync subprocess returned non-zero exit code.')
        sys.exit(EC)
    else:
        for l in r_o:
            logging.debug('RSYNC OUTPUT: ' + l)
    message(_substep('Processing symlinks, ownership, and permissions...'))
    logging.debug('Processing symlinks, ownership, and permissions...')
    for m in templates_maps:
        if m['chmod'] and not args.dry_run:
            logging.debug('Processing permissions for file "' + m['full_dst'] + '"...')
            try:
                (chmod_out, chmod_ec) = _run_process(
                    'chmod ' + m['chmod'] + " '" + m['full_dst'] + "'"
                )
            except Exception as e:
                emessage(_subsubstep('Unable to process permissions for file "' + m['full_dst'] + '" - ' + str(e) + '.', C_RED))
                logging.critical('Unable to process permissions for file "' + m['full_dst'] + '" - ' + str(e) + '.')
                sys.exit(EC)
            logging.debug('CHMOD EXIT CODE: ' + str(chmod_ec))
            if chmod_ec != 0:
                for l in chmod_out:
                    logging.critical('CHMOD OUTPUT: ' + l)
                emessage(_subsubstep('Unable to process permissions for file "' + m['full_dst'] + '" - subprocess returned non-zero exit code.', C_RED))
                logging.critical('Unable to process permissions for file "' + m['full_dst'] + '" - subprocess returned non-zero exit code.')
                sys.exit(EC)
            else:
                for l in chmod_out:
                    logging.debug('CHMOD OUTPUT: ' + l)
        if m['chown'] and not args.dry_run:
            logging.debug('Processing ownership for file "' + m['full_dst'] + '"...')
            try:
                (chown_out, chown_ec) = _run_process(
                    'chown ' + m['chown'] + " '" + m['full_dst'] + "'"
                )
            except Exception as e:
                emessage(_subsubstep('Unable to process ownership for file "' + m['full_dst'] + '" - ' + str(e) + '.', C_RED))
                logging.critical('Unable to process ownership for file "' + m['full_dst'] + '" - ' + str(e) + '.')
                sys.exit(EC)
            logging.debug('CHOWN EXIT CODE: ' + str(chown_ec))
            if chown_ec != 0:
                for l in chown_out:
                    logging.critical('CHOWN OUTPUT: ' + l)
                emessage(_subsubstep('Unable to process ownership for file "' + m['full_dst'] + '" - subprocess returned non-zero exit code.', C_RED))
                logging.critical('Unable to process ownership for file "' + m['full_dst'] + '" - subprocess returned non-zero exit code.')
                sys.exit(EC)
            else:
                for l in chown_out:
                    logging.debug('CHOWN OUTPUT: ' + l)
        if m['full_lnk'] and not args.dry_run:
            logging.debug('Processing symlink for file "' + m['full_dst'] + '"...')
            if os.path.islink(m['full_lnk']):
                logging.debug('Removing old symlink...')
                try:
                    os.unlink(m['full_lnk'])
                except Exception as e:
                    emessage(_subsubstep('Unable to process symlink for file "' + m['full_dst'] + '" - unable to remove old symlink - ' + str(e) + '.', C_RED))
                    logging.critical('Unable to process symlink for file "' + m['full_dst'] + '" - unable to remove old symlink - ' + str(e) + '.')
                    sys.exit(EC)
            elif os.path.exists(m['full_lnk']):
                    emessage(_subsubstep('Unable to process symlink for file "' + m['full_dst'] + '" - link destination is an existing file or directory.', C_RED))
                    logging.critical('Unable to process symlink for file "' + m['full_dst'] + '" - link destination is an existing file or directory.')
                    sys.exit(EC)
            full_lnk_dir = os.path.dirname(m['full_lnk'])
            if full_lnk_dir and not os.path.isdir(full_lnk_dir):
                logging.debug('Creating symlink parent directory "' + full_lnk_dir + '"...')
                try:
                    os.makedirs(full_lnk_dir)
                except Exception as e:
                    m = 'Unable to create symlink parent directory "' + full_lnk_dir + '" - ' + str(e) + '.'
                    emessage(_subsubstep(m, C_RED))
                    logging.critical(m)
                    sys.exit(EC)
            try:
                os.symlink(m['full_dst'], m['full_lnk'])
            except Exception as e:
                emessage(_subsubstep('Unable to process symlink for file "' + m['full_dst'] + '" - ' + str(e) + '.', C_RED))
                logging.critical('Unable to process symlink for file "' + m['full_dst'] + '" - ' + str(e) + '.')
                sys.exit(EC)
        
    
# --------------------------------------



# ---------- Boilerplate Magic ---------

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError) as ki:
        sys.stderr.write('Recieved keyboard interrupt!\n')
        sys.exit(100)

# --------------------------------------
