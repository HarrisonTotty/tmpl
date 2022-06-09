'''
Tests configuration functions.
'''

from unittest.mock import patch

from tmpl import config
from tmpl import utils


CONFIG_DST_ONLY = {
    'files': [
        {
            'dst': 'foo.txt'
        }
    ]
}
CONFIG_DST_ONLY_COMPLEX = {
    'files': [
        {
            'dst': 'foo.sh',
            'chmod': '+x',
            'chown': 'root:root',
            'symlink': '/usr/local/bin/foo',
            'translate': False
        }
    ]
}
CONFIG_DST_ONLY_LIST = {
    'files': [
        {
            'dst': 'foo-[a,b].txt',
        }
    ]
}
CONFIG_DST_ONLY_RANGE = {
    'files': [
        {
            'dst': 'foo[1-3].txt',
        }
    ]
}
CONFIG_LIB = {
    'lib': [
        'foo.py',
        'bar[1-3].py',
        'baz-[a,b].py'
    ],
    'template_configuration_file': '/tmp/example.yaml'
}
CONFIG_SRC_DST = {
    'files': [
        {
            'dst': 'foo.txt',
            'src': 'foo.template'
        }
    ]
}

TEMPLATE_DIR = '/tmp/src'
OUTPUT_DIR   = '/tmp/dst'
WORKING_DIR  = '/tmp/wrk'

utils.TEMPLATE_DIR = TEMPLATE_DIR

@patch('os.path.exists')
def test_compute_mapping(mock_path_exists):
    '''
    Tests config.compute_mapping()
    '''
    mock_path_exists = lambda: True
    assert config.compute_mapping(CONFIG_DST_ONLY, OUTPUT_DIR, WORKING_DIR) == [
        {
            'chmod': '',
            'chown': '',
            'dst_key': 'foo.txt',
            'full_dst': OUTPUT_DIR + '/foo.txt',
            'full_lnk': '',
            'full_src': TEMPLATE_DIR + '/foo.txt',
            'full_wrk': WORKING_DIR + '/foo.txt',
            'rel_dst': 'foo.txt',
            'rel_lnk': '',
            'rel_src': 'foo.txt',
            'translate': True
        }
    ]
    config_dst_only_complex = config.compute_mapping(CONFIG_DST_ONLY_COMPLEX, OUTPUT_DIR, WORKING_DIR)
    config_dst_only_complex[0]['rel_lnk'] = 'redacted'
    assert config_dst_only_complex == [
        {
            'chmod': '+x',
            'chown': 'root:root',
            'dst_key': 'foo.sh',
            'full_dst': OUTPUT_DIR + '/foo.sh',
            'full_lnk': '/usr/local/bin/foo',
            'full_src': TEMPLATE_DIR + '/foo.sh',
            'full_wrk': WORKING_DIR + '/foo.sh',
            'rel_dst': 'foo.sh',
            'rel_lnk': 'redacted',
            'rel_src': 'foo.sh',
            'translate': False
        }
    ]
    assert config.compute_mapping(CONFIG_DST_ONLY_LIST, OUTPUT_DIR, WORKING_DIR) == [
        {
            'chmod': '',
            'chown': '',
            'dst_key': 'foo-[a,b].txt',
            'full_dst': OUTPUT_DIR + '/foo-a.txt',
            'full_lnk': '',
            'full_src': TEMPLATE_DIR + '/foo-a.txt',
            'full_wrk': WORKING_DIR + '/foo-a.txt',
            'rel_dst': 'foo-a.txt',
            'rel_lnk': '',
            'rel_src': 'foo-a.txt',
            'translate': True
        },
        {
            'chmod': '',
            'chown': '',
            'dst_key': 'foo-[a,b].txt',
            'full_dst': OUTPUT_DIR + '/foo-b.txt',
            'full_lnk': '',
            'full_src': TEMPLATE_DIR + '/foo-b.txt',
            'full_wrk': WORKING_DIR + '/foo-b.txt',
            'rel_dst': 'foo-b.txt',
            'rel_lnk': '',
            'rel_src': 'foo-b.txt',
            'translate': True
        },
    ]
    assert config.compute_mapping(CONFIG_DST_ONLY_RANGE, OUTPUT_DIR, WORKING_DIR) == [
        {
            'chmod': '',
            'chown': '',
            'dst_key': 'foo[1-3].txt',
            'full_dst': OUTPUT_DIR + '/foo1.txt',
            'full_lnk': '',
            'full_src': TEMPLATE_DIR + '/foo1.txt',
            'full_wrk': WORKING_DIR + '/foo1.txt',
            'rel_dst': 'foo1.txt',
            'rel_lnk': '',
            'rel_src': 'foo1.txt',
            'translate': True
        },
        {
            'chmod': '',
            'chown': '',
            'dst_key': 'foo[1-3].txt',
            'full_dst': OUTPUT_DIR + '/foo2.txt',
            'full_lnk': '',
            'full_src': TEMPLATE_DIR + '/foo2.txt',
            'full_wrk': WORKING_DIR + '/foo2.txt',
            'rel_dst': 'foo2.txt',
            'rel_lnk': '',
            'rel_src': 'foo2.txt',
            'translate': True
        },
        {
            'chmod': '',
            'chown': '',
            'dst_key': 'foo[1-3].txt',
            'full_dst': OUTPUT_DIR + '/foo3.txt',
            'full_lnk': '',
            'full_src': TEMPLATE_DIR + '/foo3.txt',
            'full_wrk': WORKING_DIR + '/foo3.txt',
            'rel_dst': 'foo3.txt',
            'rel_lnk': '',
            'rel_src': 'foo3.txt',
            'translate': True
        },
    ]
    assert config.compute_mapping(CONFIG_SRC_DST, OUTPUT_DIR, WORKING_DIR) == [
        {
            'chmod': '',
            'chown': '',
            'dst_key': 'foo.txt',
            'full_dst': OUTPUT_DIR + '/foo.txt',
            'full_lnk': '',
            'full_src': TEMPLATE_DIR + '/foo.template',
            'full_wrk': WORKING_DIR + '/foo.txt',
            'rel_dst': 'foo.txt',
            'rel_lnk': '',
            'rel_src': 'foo.template',
            'translate': True
        }
    ]


def test_get_lib_paths():
    '''
    Tests config.get_lib_paths()
    '''
    assert config.get_lib_paths(CONFIG_LIB) == [
        '/tmp/foo.py',
        '/tmp/bar1.py',
        '/tmp/bar2.py',
        '/tmp/bar3.py',
        '/tmp/baz-a.py',
        '/tmp/baz-b.py',
    ]


def test_validate():
    '''
    Tests config.validate()
    '''
    config.validate(CONFIG_DST_ONLY)
    config.validate(CONFIG_DST_ONLY_COMPLEX)
    config.validate(CONFIG_DST_ONLY_LIST)
    config.validate(CONFIG_DST_ONLY_RANGE)
    config.validate(CONFIG_LIB)
    config.validate(CONFIG_SRC_DST)
