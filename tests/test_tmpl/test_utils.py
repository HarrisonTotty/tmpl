'''
Tests common utilities.
'''

from unittest.mock import patch

from tmpl import utils

utils.TEMPLATE_DIR = '/tmp/src'

def test_get_hostname():
    '''
    Tests utils.get_hostname()
    '''
    result = utils.get_hostname()
    assert isinstance(result, tuple)    == True
    assert len(result)              == 2
    assert isinstance(result[0], str) == True
    assert isinstance(result[1], str) == True

@patch('os.path.expanduser')
def test_get_path(mock_expand_user):
    '''
    Tests utils.get_path()
    '''
    mock_expand_user.side_effect = lambda x: x.replace('~', '/home/example')
    assert utils.get_path('/foo')        == '/foo'
    assert utils.get_path('~/foo')       == '/home/example/foo'
    assert utils.get_path('foo')         == '/tmp/src/foo'
    assert utils.get_path('bar', '/foo') == '/foo/bar'

def test_merge_yaml_data():
    '''
    Tests utils.merge_yaml_data()
    '''
    assert utils.merge_yaml_data('foo', 'bar')                        == 'bar'
    assert utils.merge_yaml_data(['foo'], ['bar', 'baz'])             == ['foo', 'bar', 'baz']
    assert utils.merge_yaml_data({'foo': 'bar'}, {'baz': True})          == { 'foo': 'bar', 'baz': True }
    assert utils.merge_yaml_data({'foo': True}, {'foo': False})              == { 'foo': False }
    assert utils.merge_yaml_data({'foo': ['a', 'b']}, {'foo': ['c']}) == { 'foo': ['a', 'b', 'c'] }

def test_parse_file_paths():
    '''
    Tests utils.parse_file_paths()
    '''
    assert utils.parse_file_paths('/foo/bar.txt')         == ['/foo/bar.txt']
    assert utils.parse_file_paths('/foo/bar-[a,b,c].txt') == ['/foo/bar-a.txt', '/foo/bar-b.txt', '/foo/bar-c.txt']
    assert utils.parse_file_paths('/foo/bar-[1-3].txt')   == ['/foo/bar-1.txt', '/foo/bar-2.txt', '/foo/bar-3.txt']

def test_run_process():
    '''
    Tests utils.run_process()
    '''
    assert utils.run_process('python -c "print(\'test\')"')    == (['test'], 0)
    assert utils.run_process('python -c "print(\'test\')"', False) == ('test\n', 0)
