# Configuration & Templating

`tmpl` is supplied with a _Template Configuration File_ at runtime, either explicitly or implicitly (by providing the script with a _directory_). The template configuration file is a YAML document which contains:

* Arbitrary variables which may be referenced within template files.
* Template file mappings (the location of source files to translate, and where to save them).
* Additional YAML file include statements.
* Library extension file include statements.


----
## Arbitrary Variable Definitions

Arbitrary variable definitions are exposed to template files as-is. For example, the following template configuration file

```yaml
# Primary Template Configuration File
# -----------------------------------

# My name.
name: "Harrison Totty"

# My age.
age: 26

# Some of my projects.
projects:
  - "mkdot"
  - "Remote Execution Framework"
  - "tmpl"
```

could be translated into a text file via a template like the following:

```
Hello, my name is {{ name }}. I am {{ age }} years old.

Here are some of my projects:
{% for project in projects %}
{{ project }}
{% endfor %}
```

which should result in what you'd expect.


----
## Template File Includes

A template configuration file may merge its definitions with other YAML files, whose paths are mapped as list elements in the `include` key. For example, a template configuration file which is used to build a resume might have the following form:

```yaml
# Primary Template Configuration File
# -----------------------------------

# Include additional configuration files.
include:
  - "yaml/education.yaml"
  - "yaml/experience.yaml"
  - "yaml/projects.yaml"
```

These file paths, like all most file paths in `tmpl`, are relative to the _template configuration file_ and _not_ the working directory the script was executed in.

As stated above, these files have their definitions _merged_ with the primary template, so if `foo: "bar"` is defined in `primary.yaml` and `foo: "baz"` is defined in `included.yaml`, then templates will see `foo` mapped to `"baz"`.


----
## Built-In Functions & Library Extensions

`tmpl` automatically provides several built-in Jinja functions. The following table provides a breif description for each of these functions:

| Name            | Description                                                                                                   |
|-----------------|---------------------------------------------------------------------------------------------------------------|
| `domain_join`   | Joins each argument with a single `.` character.                                                              |
| `env`           | Fetches the value of a specified environment variable, with an optional default value.                        |
| `file_ext`      | Returns the extension of the specified file path.                                                             |
| `file_name`     | Returns the name of the specified file path (without the extension).                                          |
| `get`           | Returns the value of the variable with the specified string name.                                             |
| `get_host`      | Returns the hostname associated with the specified IP address.                                                |
| `get_ip`        | Returns the IP address associated with the specified hostname.                                                |
| `get_output`    | Returns the output of the specified system shell command.                                                     |
| `parse_yaml`    | Parses the specified string as YAML, using `yaml.safe_load()` from PyYAML.                                    |
| `path_basename` | Same as `os.path.basename` in Python.                                                                         |
| `path_dirname`  | Same as `os.path.dirname` in Python.                                                                          |
| `path_join`     | Same as `os.path.join` in Python.                                                                             |
| `print`         | Prints the specified string to STDOUT during template translation.                                            |
| `raise`         | Raises an exception during template translation with the specified string value.                              |
| `read_file`     | Returns the contents of the file located at the specified path (relative to the template configuration file). |
| `require`       | Raises an exception during template translation if one of the specified variables is not defined.             |

In addition to the above functions, `tmpl` also pre-defines the following variables:

| Name                          | Description                                                                                            |
|-------------------------------|--------------------------------------------------------------------------------------------------------|
| `fqdn`                        | The fully-qualified domain name of the machine executing the script.                                   |
| `hostname`                    | The hostname of the machine executing the script.                                                      |
| `output_directory`            | The full path to the specified output directory.                                                       |
| `template_configuration_file` | The full path to the specified template configuration file.                                            |
| `this`                        | A shortcut to the definition within the `files` specification pertaining to the current template file. |

### Library Extensions

`tmpl` is designed to have its execution environment highly configurable, and thus it is possible to extend the list of functions available to the template translation environment by defining a list of library extensions via the `lib` key in the primary template configuration file. The `lib` key is mapped to a list of file paths relative to the primary template configuration file. As an example, consider the definition below:

```yaml
# Primary Template Configuration File
# -----------------------------------

# Include some library extensions.
lib:
  - "pylib/example.py"
  
# ...
```

with the contents of `pylib/example.py` being:

```python
# Library Extension
# -----------------

def print_is_foo(val):
    if val == 'foo':
        print('The value is foo!')
```

In the above example, any template translated by the above template configuration file will have access to the `print_is_foo()` function. Note that the function is _not_ accessed from a template as `example.print_is_foo()`.


----
## Template File Mappings & STDIN Mode

When running `tmpl` in "STDIN mode" (for example: `$ cat foo/some_file.template | tmpl config.yaml`), the script will simply write the translated contents of its STDIN to STDOUT. However, it is most often the case that `tmpl` is called with a template configuration file that defines a set of input-output file mappings. Such mappings are defined within the `files` key. The following template configuration file provides a high-level overview of how this works:

```yaml
# Primary Template Configuration File
# -----------------------------------

files:
    # In the most basic example, the following specification will translate a
    # source file called "foo.template" (relative to the template configuration
    # file) to a destination file called "foo.txt" (relative to the specified
    # output directory).
    - dst: "foo.txt"
      src: "foo.template"
      
    # If the input and output files have the same name, then only the "dst" key
    # need be defined.
    - dst: "bar.conf"
    
    # Multiple files may be selected in the same definition via wildcards, range
    # expressions, or list expressions (explained later in this section).
    # Furthermore, translation may be supressed altogether by specifying the
    # value of "translate" to "false" (resulting in tmpl just copying and
    # renaming files).
    - dst: "docs/*.pdf"
      translate: false
      
    # Additional keys defined for a specification may be accessed via
    # "this.KEYNAME" in the template.
    - dst: "httpd.conf"
      src: "httpd.template"
      enable_ssl: true
      server_name: "example.com"
      server_aliases:
        - "foo.example.com"
        - "bar.example.com"
        - "baz.example.com"
```

Each file mapping definition may contain any or all of the following keys (that `tmpl` will act on):

| Key         | Description                                                                                     | Example Value     |
|-------------|-------------------------------------------------------------------------------------------------|-------------------|
| `chmod`     | Sets the permissions of the destination file(s), as if set by `chmod`.                          | `"g+rw,+x"`       |
| `chown`     | Sets the ownership of the destination file(s), as if set by `chown`.                            | `"root:root"`     |
| `dst`       | (Required) The destination file name(s), including source file name(s) if `src` is not defined. | `"foo.txt"`       |
| `src`       | The source file name.                                                                           | `"foo.template"`  |
| `symlink`   | A symbolic file link to which the destination file will be mapped.                              | `"/etc/foo.conf"` |
| `translate` | Whether to translate the specified file(s), or just copy (and potentially rename) them.         | `false`           |

As stated above, any other key-value pairs will have no implicit effect, other than to be accessible in the template via the `this` key.

### File Path Conventions & Expressions

As alluded to above, file paths for keys like `include`, `lib`, or `dst`/`src` in a `files` definition may be specified via a relative path (like `"foo.txt"`) which is relative to the primary template configuration file for the `src` key and relative to the specified output directory for the `dst` key (if the `src` key is not defined, then the source file will be relative to the primary template configuration file as expected), or via an absolute path (like `"/etc/foo.txt"` or `"~/foo.txt"`). In addition to relative vs. absolute paths, each path may be expanded to multiple paths via wildcard and list/range expressions:

* A _wildcard expression_ (or _glob expression_) matches files in the same way that a shell would match them. For example, `"foo*.txt"` would match `["foo1.txt", "foo-bar.txt", ...]`.

* A _range expression_ matches files according to a specified integer range defined in the form `[x-y]`, where `x` is the lower-bound of the range and `y` is the upper-bound (inclusive). For example, `"foo[1-3].txt"` would match `["foo1.txt", "foo2.txt", "foo3.txt"]`.

* A _list expression_ matches files according to a specified subset list of character sequences in the form `[a,b,c,...]`. For example, `"foo-[bar,baz].txt"` would match `["foo-bar.txt", "foo-baz.txt"]`.

