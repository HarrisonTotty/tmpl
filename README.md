# Introduction

`tmpl` is a Python script that serves as a general-purpose templating engine on top of Jinja2 and YAML. It was designed to be extendable, all-encompassing, and not completely garbage.


## System Requirements

* Python 3
* [Jinja2](http://jinja.pocoo.org/)
* [PyYAML](https://pyyaml.org/)
* `rsync`


## Installation

There is currently no installer, but you should be able to get by with something like:

```bash
$ ln -s /path/to/repo/tmpl.py /usr/local/bin/tmpl
```


## Known Bugs and Potential Issues

* `tmpl` doesn't currently support recursive YAML imports. Only the primary configuration file may import additional files, however you _can_ load configuration files at "runtime" via something like `{% set data = parse_yaml(read_file('foo.yaml')) %}`.
* Currently only _one_ substitution of the form `*`, `[a,b,c...]`, or `[x-y]` may be used in file paths.


----
# Usage


## Basic Example

`tmpl` is typically invoked by specifying the location of a _Template Configuration File_ to load (See `CONFIGURATION.md`). If a directory is supplied instead of a full path, `tmpl` will select a file within that directory called `tmpl.yaml` or `tmpl.yml`, or select the `.y*ml` file that most closely matches the hostname of the executing machine. With regards to this repository, the example templates may be rendered via executing:

```bash
$ tmpl example
```

By default, `tmpl` will render templates into the current working directory, so it is often beneficial to pass a value to the `-o`/`--output` option of the script.

In the above example, `example/tmpl.yaml` contains a `files` key, which tells `tmpl` where to look for template files and how to translate them. `tmpl` also supports rendering raw Jinja templating that has been passed to its standard input, in which it will write the resulting text to standard output. Again with respect to this repository, a simple example might look like:

```bash
$ cat example/stdin.test | tmpl example > stdout.test
```


## CLI Arguments

The following table describes the various command-line arguments:

| Argument(s)                 | Description                                                                                                                                                                |
|-----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--block-end-string`        | Specifies the string marking the end of a Jinja template block.                                                                                                            |
| `--block-start-string`      | Specifies the string marking the start of a Jinja template block.                                                                                                          |
| `--comment-end-string`      | Specifies the string marking the end of a Jinja template comment.                                                                                                          |
| `--comment-start-string`    | Specifies the string marking the start of a Jinja template comment.                                                                                                        |
| `--delete`                  | Specifies that the script should delete any files in the output directory that are not part of the list of generated files.                                                |
| `--dont-trim-blocks`        | Specifies that the first newline character after a Jinja block should NOT be removed.                                                                                      |
| `-d`, `--dry-run`           | Specifies that the script should only execute a dry-run, preventing the generated files from being copied from the working directory to the output directory.              |
| `--exclude`                 | Specifies an additional list of files or directories relative to the specified output directory that should be preserved on write if `--delete` is supplied to the script. |
| `-h`, `--help`              | Displays help and usage information.                                                                                                                                       |
| `-f`, `--log-file`          | Specifies a log file to write to in addition to stdout/stderr.                                                                                                             |
| `-l`, `--log-level`         | Specifies the log level of the script. This option is ignored if `--log-file` is not specified.                                                                            |
| `-m`, `--log-mode`          | Specifies whether to `append` or `overwrite` the specified log file. This option is ignored if `--log-file` is not specified.                                              |
| `--no-color`                | Disables colored output.                                                                                                                                                   |
| `-o`, `--output`            | Specifies the output directory of the generated files.                                                                                                                     |
| `--rsync-executable`        | Specifies a file path to the `rsync` executable utilized in transferring directories.                                                                                      |
| `--variable-end-string`     | Specifies the string marking the end of a Jinja template variable.                                                                                                         |
| `--variable-start-string`   | Specifies the string marking the start of a Jinja template variable.                                                                                                       |
| `-w`, `--working-directory` | Specifies the working directory.                                                                                                                                           |

The following table expands upon the one above to list the value types, default values, and associated environment variables for applicable arguments:

| Argument(s)                 | Value Type / Possible Values | Default Value       | Associated Environment Variable |
|-----------------------------|------------------------------|---------------------|---------------------------------|
| `--block-end-string`        | String                       | `%}`                | `TMPL_BLOCK_END_STR`            |
| `--block-start-string`      | String                       | `{%`                | `TMPL_BLOCK_START_STR`          |
| `--comment-end-string`      | String                       | `#}`                | `TMPL_COMMENT_END_STR`          |
| `--comment-start-string`    | String                       | `{#`                | `TMPL_COMMENT_START_STR`        |
| `--exclude`                 | File Path(s)                 |                     | `TMPL_EXCLUDE`                  |
| `-f`, `--log-file`          | File Path                    |                     | `TMPL_LOG_FILE`                 |
| `-l`, `--log-level`         | `info` or `debug`            | `info`              | `TMPL_LOG_LEVEL`                |
| `-m`, `--log-mode`          | `append` or `overwrite`      | `append`            | `TMPL_LOG_MODE`                 |
| `-o`, `--output`            | Directory Path               | (Current Directory) | `TMPL_OUTPUT`                   |
| `--rsync-executable`        | File Path                    | `/usr/bin/rsync`    | `TMPL_RSYNC_PATH`               |
| `--variable-end-string`     | String                       | `}}`                | `TMPL_VAR_END_STR`              |
| `--variable-start-string`   | String                       | `{{`                | `TMPL_VAR_START_STR`            |
| `-w`, `--working-directory` | Directory Path               | `/tmp/tmpl`         | `TMPL_WORKING_DIR`              |


## Exit Codes

`tmpl` may produce one of the following exit codes:

| Exit Code | Description                                                                                            |
|-----------|--------------------------------------------------------------------------------------------------------|
| `0`       | Script exited successfully, although perhaps with warnings.                                            |
| `1`       | Script encountered a general error prior to performing its main task.                                  |
| `2`       | Indicates an issue during the parsing of command-line arguments or environment validation.             |
| `3`       | Indicates an issue reading/parsing the specified template configuration file.                          |
| `4`       | Indicates an invalid template configuration file.                                                      |
| `5`       | Indicates an issue instantiating the Jinja templating engine.                                          |
| `6`       | Script was unable to determine or approve the template file path mapping.                              |
| `7`       | Script was unable to translate the templates into their final form.                                    |
| `8`       | Script failed to transfer the generated files to the specified output directory, set permissions, etc. |
| `9`       | Script failed to handle a Jinja template string passed to its standard input.                          |
