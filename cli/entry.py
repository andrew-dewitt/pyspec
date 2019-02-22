#!/usr/bin/env python
"""
entry point for the pyspec program
"""

import sys
from cli import run_tests
from api import describe

def main():
    """
    entry point for the pyspec program
    """

    print('in entry.main()')
    args = sys.argv[1:]
    for arg in args:
        print(f'passed arg: {arg}')

    def all_tests(path):
        run_tests.all_tests(path)

    def one_file(path):
        run_tests.one_file(path)

    options = {
        'all': all_tests,
        'one': one_file
    }

    options[args[0]](args[1])