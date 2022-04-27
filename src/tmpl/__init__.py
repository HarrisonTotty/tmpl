#!/usr/bin/env python3
'''
tmpl

A general-purpose templating engine.
'''

import logging
import jinja2
import os
import shutil
import sys
import yaml
from typing import Any

from . import cli
from . import config
from . import jengine
from . import utils

def bail(msg: str, ec: int):
    '''
    A handy function for reporting a critical issue.
    '''
    cli.stderr(cli.fcolor(f'ERROR: {msg}', cli.C_RED))
    logging.critical(msg)
    sys.exit(ec)


def main():
    '''
    The entrypoint of the program.
    '''
    # Parse command-line arguments.
    args = cli.parse_arguments()

    # Setup logging module.
    utils.setup_logging(args)

    # Log CLI arguments at debug level.
    logging.debug('---------- CLI Arguments ----------')
    dargs = vars(args)
    for a in dargs:
        logging.debug(a + ' : ' + str(dargs[a]))
    logging.debug('-----------------------------------')

    # Set module global variables.
    logging.debug('--------- Global Variables --------')
    cli.COLOR_OUTPUT = args.color_output
    logging.debug(f'{cli.COLOR_OUTPUT=}')
    cli.SUPPRESS_OUTPUT = args.stdin
    logging.debug(f'{cli.SUPPRESS_OUTPUT=}')
    logging.debug('-----------------------------------')

    logging.info('Starting process...')

    # Set-up and validate the environment.
    template_dir = validate_environment(args)
    utils.TEMPLATE_DIR = template_dir
    logging.debug(f'{utils.TEMPLATE_DIR=}')

    # Parse the template configuration file.
    try:
        conf = config.parse(args.template_conf)
        logging.debug('---------- Template Configuration File ----------')
        for line in yaml.dump(conf).splitlines():
            logging.debug(line)
        logging.debug('-------------------------------------------------')
    except Exception as e:
        bail(f'Unable to parse template configuration file - {e}', 3)

    # Validate the template configuration file.
    try:
        config.validate(conf)
    except Exception as e:
        bail(f'Unable to validate template configuration file - {e}', 4)

    # Set-up the jinja engine.
    try:
        jinja_engine = jengine.setup(args, template_dir)
    except Exception as e:
        bail(f'Unable to initialize jinja engine - {e}', 5)

    # Set some additional global variables.
    (hostname, fqdn) = utils.get_hostname()
    jinja_engine.globals['fqdn'] = fqdn
    jinja_engine.globals['hostname'] = hostname
    jinja_engine.globals['output_directory'] = os.path.realpath(args.output)

    # Import library extensions.
    try:
        for l in config.get_lib_paths(conf):
            jengine.import_lib(jinja_engine, l)
    except Exception as e:
        bail(f'Unable to load library extensions - {e}', 6)

    if not args.stdin:
        # Compute path template mapping.
        try:
            mapping = config.compute_mapping(conf, args.output, args.working_directory)
        except Exception as e:
            bail(str(e), 7)

        # Translate templates.
        translate_templates(jinja_engine, conf, mapping)

        # Write output.
        write_output(args, mapping)
    else:
        # Handle STDIN
        translate_stdin(jinja_engine, conf)

    logging.info('Process complete.')
    sys.exit(0)


def translate_stdin(jinja_engine: Any, conf: dict):
    '''
    Translates a Jinja string passed to STDIN to STDOUT.
    '''
    EC = 11
    logging.info('Translating from STDIN...')
    try:
        stdin = sys.stdin.read()
    except Exception as e:
        bail(f'Unable to read from STDIN - {e}', EC)
    try:
        template = jinja_engine.from_string(stdin)
    except Exception as e:
        bail(f'Unable to initialize Jinja template from STDIN - {e}', EC)
    try:
        rendered = template.render(**conf)
    except jinja2.TemplateSyntaxError as e:
        bail(f'Unable to render template from STDIN - syntax error on line {e.lineno} - {e}', EC)
    except Exception as e:
        bail(f'Unable to render template from STDIN - {e}', EC)
    print(rendered)


def translate_templates(jinja_engine: Any, conf: dict, mapping: list[dict]):
    '''
    Translates the source templates into their final forms within the working
    directory.
    '''
    EC = 8
    cli.stdout(cli.fstep('Translating templates...'))
    logging.info('Translating templates...')
    for spec in conf['files']:
        cli.stdout(cli.fsubstep(spec['dst']))
        spec_maps = [m for m in mapping if m['dst_key'] == spec['dst']]
        for spec_map in spec_maps:
            if spec_map['translate']:
                logging.info(f"Translating \"{spec_map['full_src']}\" into \"{spec_map['full_wrk']}\"...")
                logging.debug(f"Loading template \"{spec_map['rel_src']}\"...")
                try:
                    template = jinja_engine.get_template(spec_map['rel_src'])
                except jinja2.TemplateSyntaxError as e:
                    m = f"Unable to load template \"{spec_map['rel_src']}\" - syntax error on line {e.lineno} - {e}"
                    cli.stderr(cli.fcolor(f'      ERROR: {m}', cli.C_RED))
                    logging.critical(m)
                    sys.exit(EC)
                except Exception as e:
                    m = f"Unable to load template \"{spec_map['rel_src']}\" - {e}"
                    cli.stderr(cli.fcolor(f'      ERROR: {m}', cli.C_RED))
                    logging.critical(m)
                    sys.exit(EC)
                aug = conf.copy()
                aug['file'] = os.path.basename(spec_map['rel_dst'])
                aug['this'] = spec
                logging.debug(f"Rendering template \"{spec_map['rel_src']}\"...")
                try:
                    rendered = template.render(**aug)
                except jinja2.TemplateSyntaxError as e:
                    m = f"Unable to render template \"{spec_map['rel_src']}\" - syntax error on line {e.lineno} - {e}"
                    cli.stderr(cli.fcolor(f'      ERROR: {m}', cli.C_RED))
                    logging.critical(m)
                    sys.exit(EC)
                except Exception as e:
                    m = f"Unable to render template \"{spec_map['rel_src']}\" - {e}"
                    cli.stderr(cli.fcolor(f'      ERROR: {m}', cli.C_RED))
                    logging.critical(m)
                    sys.exit(EC)
                parent_dir = os.path.dirname(spec_map['full_wrk'])
                if not os.path.isdir(parent_dir):
                    try:
                        os.makedirs(parent_dir)
                    except Exception as e:
                        m = f"Unable to write \"{spec_map['rel_dst']}\" to working directory - unable to create parent directory \"{parent_dir}\" - {e}"
                        cli.stderr(cli.fcolor(f'      ERROR: {m}', cli.C_RED))
                        logging.critical(m)
                        sys.exit(EC)
                try:
                    with open(spec_map['full_wrk'], 'w') as f:
                        f.write(rendered)
                except Exception as e:
                    m = f"Unable to write \"{spec_map['rel_dst']}\" to working directory - {e}"
                    cli.stderr(cli.fcolor(f'      ERROR: {m}', cli.C_RED))
                    logging.critical(m)
                    sys.exit(EC)
            else:
                logging.info(f"Copying \"{spec_map['full_src']}\" to \"{spec_map['full_wrk']}\"...")
                parent_dir = os.path.dirname(spec_map['full_wrk'])
                if not os.path.isdir(parent_dir):
                    try:
                        os.makedirs(parent_dir)
                    except Exception as e:
                        m = f"Unable to copy \"{spec_map['rel_dst']}\" to working directory - unable to create parent directory \"{parent_dir}\" - {e}"
                        cli.stderr(cli.fcolor(f'      ERROR: {m}', cli.C_RED))
                        logging.critical(m)
                        sys.exit(EC)
                try:
                    shutil.copyfile(spec_map['full_src'], spec_map['full_wrk'])
                except Exception as e:
                    m = f"Unable to copy \"{spec_map['rel_dst']}\" to working directory - {e}"
                    cli.stderr(cli.fcolor(f'      ERROR: {m}', cli.C_RED))
                    logging.critical(m)
                    sys.exit(EC)


def validate_environment(args: Any):
    '''
    Validates that the executing environment is sufficient to proceed. In
    addition, this function also returns the selected template directory.
    '''
    EC = 2
    logging.debug('Validating working environment...')
    if not os.path.isfile(args.rsync_executable):
        bail(f'Specified rsync executable path "{args.rsync_executable}" does not exist.', EC)
    if args.base_dir and not os.path.isdir(args.base_dir):
        bail(f'Specified template base directory "{args.base_dir}" does not exist.', EC)
    if not os.path.isfile(args.template_conf):
        if not os.path.isdir(args.template_conf):
            bail(f'Specified template configuration path "{args.template_conf}" does not exist.', EC)
        else:
            logging.debug('Selecting a suitable template configuration file within the specified directory...')
            files = [f for f in os.listdir(args.template_conf) if os.path.isfile(os.path.join(args.template_conf, f))]
            (hostname, fqdn) = utils.get_hostname()
            simple_matches = ['tmpl.yaml', 'tmpl.yml', f'{fqdn}.yaml', f'{fqdn}.yml', f'{hostname}.yaml', f'{hostname}.yml']
            if not files:
                bail(f'Specified template configuration file directory "{args.template_conf}" does not contain any template configuration files.', EC)
            elif any(x in files for x in simple_matches):
                args.template_conf = os.path.join(
                    args.template_conf,
                    next(x for x in simple_matches if x in files)
                )
            elif any(((f.endswith('.yaml') or f.endswith('.yml')) and f.rsplit('.', 1)[0] in hostname) for f in files):
                args.template_conf = os.path.join(
                    args.template_conf,
                    next(f for f in files if (f.endswith('.yaml') or f.endswith('.yml')) and f.rsplit('.', 1)[0] in hostname)
                )
            else:
                bail(f'Specified template configuration file directory "{args.template_conf}" does not contain any selectable template configuration files.', EC)
        logging.info(f'Automatically selected template configuration file "{args.template_conf}".')
    if os.path.isfile(args.working_directory):
        bail(f'Specified working directory "{args.working_directory}" is an existing file.', EC)
    if os.path.isdir(args.working_directory):
        try:
            shutil.rmtree(args.working_directory)
        except Exception as e:
            bail(f'Unable to delete previous working directory - {e}', EC)
    try:
        os.makedirs(args.working_directory)
    except Exception as e:
        bail(f'Unable to create working directory - {e}', EC)
    if not args.base_dir:
        return os.path.dirname(args.template_conf)
    else:
        return args.base_dir


def write_output(args: Any, mapping: list[dict]):
    '''
    Transfers the newly generated files from the working directory to the specified output directory.
    '''
    EC = 9
    msg = 'Finalizing translation process'
    if args.dry_run: msg += ' (DRY RUN)'
    cli.stdout(cli.fstep(f'{msg}...'))
    logging.debug(f'{msg}...')
    if not os.path.isdir(args.output):
        msg = f'Creating output directory "{args.output}"...'
        cli.stdout(cli.fsubstep(msg))
        logging.debug(msg)
        try:
            if not args.dry_run: os.makedirs(args.output)
        except Exception as e:
            bail(f'Unable to create output directory - {e}', EC)
    msg = 'Transferring files to output directory...'
    cli.stdout(cli.fsubstep(msg))
    logging.debug(msg)
    rsync_args = '-a -h --progress'
    if args.delete: rsync_args += ' --delete'
    if args.dry_run: rsync_args += ' --dry-run'
    if args.exclude and args.exclude[0]:
        for x in args.exclude:
            rsync_args += ' --exclude ' + x
    logging.debug(f'{rsync_args=}')
    rsync_src = args.working_directory.rstrip('/') + '/'
    logging.debug(f'{rsync_src}')
    rsync_dst = args.output.rstrip('/') + '/'
    logging.debug(f'{rsync_dst}')
    try:
        (rsync_output, rsync_ec) = utils.run_process(
            f'{args.rsync_executable} {rsync_args} "{rsync_src}" "{rsync_dst}"'
        )
    except Exception as e:
        bail(f'Unable to transfer files to output directory - {e}', EC)
    logging.debug(f'{rsync_ec=}')
    logf = logging.critical if rsync_ec else logging.debug
    for l in rsync_output: logf(f'RSYNC OUTPUT: {l}')
    if rsync_ec:
        bail(f'Unable to transfer files to output directory - rsync subprocess returned non-zero exit code "{rsync_ec}"', EC)
    EC = 10
    msg = 'Processing symlinks, ownership, and permissions...'
    cli.stdout(cli.fsubstep(msg))
    logging.debug(msg)
    for m in mapping:
        full_dst = m['full_dst']
        chmod = m['chmod']
        chown = m['chown']
        symlink = m['full_lnk']
        if args.chmod and chmod and not args.dry_run:
            logging.debug(f'Setting permissions of "{full_dst}" to "{chmod}"...')
            try:
                (chmod_output, chmod_ec) = utils.run_process(
                    f'chmod {chmod} "{full_dst}"'
                )
            except Exception as e:
                bail(f'Unable to set permissions of "{full_dst}" to "{chmod}" - {e}', EC)
            logging.debug(f'{chmod_ec=}')
            logf = logging.critical if chmod_ec else logging.debug
            for l in chmod_output: logf(f'CHMOD OUTPUT: {l}')
            if chmod_ec:
                bail(f'Unable to set permissions of "{full_dst}" to "{chmod}" - chmod subprocess returned non-zero exit code "{chmod_ec}"', EC)
        if args.chown and chown and not args.dry_run:
            logging.debug(f'Setting ownership of "{full_dst}" to "{chown}"...')
            try:
                (chown_output, chown_ec) = utils.run_process(
                    f'chown {chown} "{full_dst}"'
                )
            except Exception as e:
                bail(f'Unable to set ownership of "{full_dst}" to "{chown}" - {e}', EC)
            logging.debug(f'{chown_ec=}')
            logf = logging.critical if chown_ec else logging.debug
            for l in chown_output: logf(f'CHOWN OUTPUT: {l}')
            if chown_ec:
                bail(f'Unable to set ownership of "{full_dst}" to "{chown}" - chown subprocess returned non-zero exit code "{chown_ec}"', EC)
        if args.symlinks and symlink and not args.dry_run:
            if os.path.islink(symlink):
                logging.debug(f'Removing existing symlink "{symlink}" for file "{full_dst}"...')
                try:
                    os.unlink(symlink)
                except Exception as e:
                    bail(f'Unable to remove existing symlink "{symlink}" - {e}', EC)
            elif os.path.exists(symlink):
                bail(f'Link destination "{symlink}" for file "{full_dst}" is an existing regular file or directory', EC)
            full_lnk_dir = os.path.dirname(symlink)
            if full_lnk_dir and not os.path.isdir(full_lnk_dir):
                logging.debug(f'Creating parent directory of symlink "{symlink}" for "{full_dst}"...')
                try:
                    os.makedirs(full_lnk_dir)
                except Exception as e:
                    bail(f'Unable to create parent directory of symlink "{symlink}" for "{full_dst}" - {e}', EC)
            logging.debug(f'Linking "{symlink}" to "{full_dst}"...')
            try:
                os.symlink(full_dst, symlink)
            except Exception as e:
                bail(f'Unable to create symlink "{symlink}" for "{full_dst}"...', EC)
