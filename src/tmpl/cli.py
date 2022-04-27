#!/usr/bin/env python3
'''
Contains functions for interacting with the CLI.
'''

import argparse
import os
import sys
from typing import Any


C_BLUE   = '\033[94m'
C_GREEN  = '\033[92m'
C_ORANGE = '\033[93m'
C_RED    = '\033[91m'
C_END    = '\033[0m'
C_BOLD   = '\033[1m'
COLOR_OUTPUT = True
COLORS = [C_BLUE, C_GREEN, C_ORANGE, C_RED, C_END, C_BOLD]
HELP_DESCRIPTION = """
A highly-configurable general-purpose templating program.
"""
HELP_EPILOG = """
"""
SUPPRESS_OUTPUT = False


def fcolor(instring: str, color: str = C_BLUE) -> str:
    '''
    Colorizes the specified string.
    '''
    if COLOR_OUTPUT and not color is None:
        return color + instring + C_END
    else:
        return instring


def fstep(instring: str, color: str = C_BLUE) -> str:
    '''
    Formats the specified string as a "step".
    '''
    return fcolor('::', color) + ' ' + fcolor(instring, C_BOLD)


def fsubstep(instring: str, color: str = C_BLUE) -> str:
    '''
    Formats the specified string as a "sub-step".
    '''
    return '  ' + fcolor('-->', color) + ' ' + instring


def fsubsubstep(instring: str, color: str = None) -> str:
    '''
    Formats the specified string as a "sub-sub-step".
    '''
    return '      ' + fcolor(instring, color)


def parse_arguments() -> Any:
    '''
    Parses the command-line arguments passed to the script, returning the
    result.
    '''
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
        '--no-chmod',
        action = 'store_false',
        dest = 'chmod',
        help = 'Disables file permissions setting functionality.'
    )
    argparser.add_argument(
        '--no-chown',
        action = 'store_false',
        dest = 'chown',
        help = 'Disables file ownership setting functionality.'
    )
    argparser.add_argument(
        '--no-color',
        action = 'store_false',
        dest = 'color_output',
        help = 'Disables color output to stdout/stderr.'
    )
    argparser.add_argument(
        '--no-symlinks',
        action = 'store_false',
        dest = 'symlinks',
        help = 'Disables file symlink functionality.'
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
    return argparser.parse_args()


def stderr(instring: str):
    '''
    Prints the specified message to STDOUT.
    '''
    if not SUPPRESS_OUTPUT: sys.stderr.write(instring + '\n')


def stdout(instring: str):
    '''
    Prints the specified message to STDOUT.
    '''
    if not SUPPRESS_OUTPUT: print(instring)
