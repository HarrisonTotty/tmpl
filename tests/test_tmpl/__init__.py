'''
Module Unit Tests

For the most part this file just contains common resources leveraged by other
test files.
'''

import pytest

import tmpl


# ----- Module-Wide Tests -----
def test_module_name():
    '''
    Tests the name of the module.
    '''
    assert tmpl.__name__ == 'tmpl'
