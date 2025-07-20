#!/usr/bin/env python3
"""
tmpl

A general-purpose templating engine.
"""

from pathlib import Path
from typing import Optional

import click

HELP = """
A highly configurable general-purpose templating utility.
"""

EPILOG = """
"""

LOG_LEVELS = [
    "TRACE",
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL"
]

@click.command(
    name="tmpl",
    context_settings = {
        "help_option_names": ["-h", "--help"],
        "max_content_width": 120,
        "show_default": True
    },
    help=HELP,
    epilog=EPILOG
)
@click.argument(
    'template_config',
    type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "-b",
    "--base-dir",
    envvar="TMPL_BASE_DIR",
    help="[env: TMPL_BASE_DIR] The base directory from which the template files will be loaded. Defaults to the directory containing the specified template configuration file.",
    metavar="DIR",
    type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.option(
    "--block-end",
    default="%}",
    envvar="TMPL_BLOCK_END",
    help="[env: TMPL_BLOCK_END] The string denoting the end of a template block.",
    metavar="STR",
    type=str
)
@click.option(
    "--block-start",
    default="{%",
    envvar="TMPL_BLOCK_START",
    help="[env: TMPL_BLOCK_START] The string denoting the start of a template block.",
    metavar="STR",
    type=str
)
@click.option(
    "--comment-end",
    default="#}",
    envvar="TMPL_COMMENT_END",
    help="[env: TMPL_COMMENT_END] The string denoting the end of a template comment.",
    metavar="STR",
    type=str
)
@click.option(
    "--comment-start",
    default="{#",
    envvar="TMPL_COMMENT_START",
    help="[env: TMPL_COMMENT_START] The string denoting the start of a template comment.",
    metavar="STR",
    type=str
)
@click.option(
    "--delete",
    help="Specifies that the utility to should delete any files in the output directory that are not part of the generated files. Certain files and directories may be preserved with the \"--exclude\" option.",
    is_flag=True
)
@click.option(
    "-d",
    "--dry-run",
    help="Instructs the script to not make any changes to the output directory.",
    is_flag=True
)
@click.option(
    "--exclude",
    envvar="TMPL_EXCLUDE",
    help="[env: TMPL_EXCLUDE] Additional files or directories (relative to the output directory) that should be preserved when running the program with the \"--delete\" flag.",
    metavar="PATH",
    multiple=True
)
@click.option(
    "-f",
    "--log-file",
    envvar="TMPL_LOG_FILE",
    help="[env: TMPL_LOG_FILE] A path to write log entries to in addition to stdout/stderr.",
    metavar="DIR",
    type=click.Path(dir_okay=False, path_type=Path)
)
@click.option(
    "-l",
    "--log-level",
    default="info",
    envvar="TMPL_LOG_LEVEL",
    help='[env: TMPL_LOG_LEVEL] The log level of the program. Accepts "trace", "debug", "info", "warning", "error", or "critical".',
    metavar="LVL",
    type=click.Choice(LOG_LEVELS, case_sensitive=False)
)
@click.option(
    "-m",
    "--log-mode",
    default="append",
    envvar="TMPL_LOG_MODE",
    help='[env: TMPL_LOG_MODE] The logging mode of the program. Accepts "append" or "overwrite".',
    metavar="MODE",
    type=click.Choice(["append", "overwrite"], case_sensitive=False)
)
@click.option(
    "--chmod/--no-chmod",
    default=True,
    help="Enables or disables the file permission management functionality of the program.",
    is_flag=True
)
@click.option(
    "--chown/--no-chown",
    default=True,
    help="Enables or disables the file ownership management functionality of the program.",
    is_flag=True
)
@click.option(
    "--color/--no-color",
    default=True,
    help="Whether to enable color output.",
    is_flag=True
)
@click.option(
    "-o",
    "--output",
    envvar="TMPL_OUTPUT",
    help="[env: TMPL_OUTPUT] The output directory within which to save the generated files.",
    metavar="DIR",
    type=click.Path(file_okay=False, path_type=Path)
)
@click.option(
    "--symlinks/--no-symlinks",
    default=True,
    help="Whether to enable the symlink functionality of the program.",
    is_flag=True
)
@click.option(
    "--trim-blocks/--no-trim-blocks",
    default=True,
    help="Specifies whether the utility should remove the first newline character after jinja blocks.",
    is_flag=True
)
@click.option(
    "--var-end",
    default="}}",
    envvar="TMPL_VAR_END",
    help="[env: TMPL_VAR_END] The string denoting the end of a template variable.",
    metavar="STR",
    type=str
)
@click.option(
    "--var-start",
    default="{{",
    envvar="TMPL_VAR_START",
    help="[env: TMPL_VAR_START] The string denoting the start of a template variable.",
    metavar="STR",
    type=str
)
@click.option(
    "-w",
    "--work-dir",
    default="/tmp/tmpl",
    envvar="TMPL_WORK_DIR",
    help="[env: TMPL_WORK_DIR] The working directory to use when generating output files.",
    metavar="DIR",
    type=click.Path(file_okay=False, path_type=Path)
)
def main(
    template_config: Path,
    base_dir: Optional[Path],
    block_end: str,
    block_start: str,
    comment_end: str,
    comment_start: str,
    delete: bool,
    dry_run: bool,
    exclude: list[str],
    log_file: Optional[Path],
    log_level: str,
    log_mode: str,
    chmod: bool,
    chown: bool,
    color: bool,
    symlinks: bool,
    trim_blocks: bool,
    var_end: str,
    var_start: str,
    work_dir: Path
) -> None:
    """
    The entrypoint of the program.
    """
    init_logging(log_file, log_level, log_mode)

def init_logging(log_file: Optional[Path], log_level: str, log_mode: str) -> None:
    """
    Sets up the logging of the program.
    """
