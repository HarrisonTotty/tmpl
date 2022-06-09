'''
Tests tmpl CLI functions.
'''

from tmpl import cli

def test_fcolor():
    '''
    Tests cli.fcolor()
    '''
    assert cli.fcolor('test')            == cli.C_BLUE + 'test' + cli.C_END
    assert cli.fcolor('test', cli.C_RED) == cli.C_RED + 'test' + cli.C_END
    assert cli.fcolor('test', None)         == 'test'

def test_fstep():
    '''
    Tests cli.fstep()
    '''
    assert cli.fstep('test')            == cli.C_BLUE + '::' + cli.C_END + ' ' + cli.C_BOLD + 'test' + cli.C_END
    assert cli.fstep('test', cli.C_RED) == cli.C_RED + '::' + cli.C_END + ' ' + cli.C_BOLD + 'test' + cli.C_END
    assert cli.fstep('test', None)         == ':: ' + cli.C_BOLD + 'test' + cli.C_END

def test_fsubstep():
    '''
    Tests cli.fsubstep()
    '''
    assert cli.fsubstep('test')            == '  ' + cli.C_BLUE + '-->' + cli.C_END + ' test'
    assert cli.fsubstep('test', cli.C_RED) == '  ' + cli.C_RED + '-->' + cli.C_END + ' test'
    assert cli.fsubstep('test', None)         == '  --> test'

def test_fsubsubstep():
    '''
    Tests cli.fsubsubstep()
    '''
    assert cli.fsubsubstep('test')            == '      test'
    assert cli.fsubsubstep('test', cli.C_RED) == '      ' + cli.C_RED + 'test' + cli.C_END
    assert cli.fsubsubstep('test', None)         == '      test'
