'''
Tests tmpl-provided jinja functions.
'''

from tmpl import jfuncs

EXAMPLE_YAML = '''
foo:
  bar:
   - baz
   - whamzo
'''

def test_domain_join():
    '''
    Tests jfuncs.t_domain_join()
    '''
    assert jfuncs.t_domain_join('www', 'example', 'com')   == 'www.example.com'
    assert jfuncs.t_domain_join('www.', 'example', '.com') == 'www.example.com'

def test_env():
    '''
    Tests jfuncs.t_env()
    '''
    assert jfuncs.t_env('DOES_NOT_EXIST', 'foo') == 'foo'

def test_file_ext():
    '''
    Tests jfuncs.t_file_ext()
    '''
    assert jfuncs.t_file_ext('baz')                 == ''
    assert jfuncs.t_file_ext('baz.txt')             == 'txt'
    assert jfuncs.t_file_ext('baz.tar.gz')          == 'tar.gz'
    assert jfuncs.t_file_ext('/foo/bar/baz')        == ''
    assert jfuncs.t_file_ext('/foo/bar/baz.txt')    == 'txt'
    assert jfuncs.t_file_ext('/foo/bar/baz.tar.gz') == 'tar.gz'

def test_file_name():
    '''
    Tests jfuncs.t_file_name()
    '''
    assert jfuncs.t_file_name('baz')                 == 'baz'
    assert jfuncs.t_file_name('baz.txt')             == 'baz'
    assert jfuncs.t_file_name('baz.tar.gz')          == 'baz'
    assert jfuncs.t_file_name('/foo/bar/baz')        == 'baz'
    assert jfuncs.t_file_name('/foo/bar/baz.txt')    == 'baz'
    assert jfuncs.t_file_name('/foo/bar/baz.tar.gz') == 'baz'

def test_parse_yaml():
    '''
    Tests jfuncs.t_parse_yaml()
    '''
    assert jfuncs.t_parse_yaml(EXAMPLE_YAML) == { 'foo': { 'bar': ['baz', 'whamzo'] } }

def test_path_basename():
    '''
    Tests jfuncs.t_path_basename()
    '''
    assert jfuncs.t_path_basename('baz')                 == 'baz'
    assert jfuncs.t_path_basename('baz.txt')             == 'baz.txt'
    assert jfuncs.t_path_basename('baz.tar.gz')          == 'baz.tar.gz'
    assert jfuncs.t_path_basename('/foo/bar/baz')        == 'baz'
    assert jfuncs.t_path_basename('/foo/bar/baz.txt')    == 'baz.txt'
    assert jfuncs.t_path_basename('/foo/bar/baz.tar.gz') == 'baz.tar.gz'

def test_path_dirname():
    '''
    Tests jfuncs.t_path_dirname()
    '''
    assert jfuncs.t_path_dirname('baz')                 == ''
    assert jfuncs.t_path_dirname('baz.txt')             == ''
    assert jfuncs.t_path_dirname('baz.tar.gz')          == ''
    assert jfuncs.t_path_dirname('/foo/bar/baz')        == '/foo/bar'
    assert jfuncs.t_path_dirname('/foo/bar/baz.txt')    == '/foo/bar'
    assert jfuncs.t_path_dirname('/foo/bar/baz.tar.gz') == '/foo/bar'

def test_path_join():
    '''
    Tests jfuncs.t_path_join()
    '''
    assert jfuncs.t_path_join('foo', 'bar')  == 'foo/bar'
    assert jfuncs.t_path_join('/foo', 'bar') == '/foo/bar'
    assert jfuncs.t_path_join('foo', '/bar') == '/bar'
