# -*- mode: python; coding: utf-8 -*-
#
# Copyright (c) 2014 Andrej Antonov <polymorphm@gmail.com>.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

assert str is not bytes

import sys
import os, os.path
import argparse
from . import safe_run
from . import lor_registrator

def main():
    parser = argparse.ArgumentParser(
            description='utility for registration on web-site '
                    '``www.linux.org.ru`` with using ``antigate`` service.',
            )
    
    parser.add_argument(
            'antigate',
            metavar='ANTIGATE-KEY-ENV',
            help='system environ variable name with antigate key',
            )
    
    args = parser.parse_args()
    
    if args.antigate not in os.environ:
        print(
                'argument error: variable {!r} not found in system environ'.format(
                        args.antigate,
                        ),
                file=sys.stderr,
                )
        exit(code=2)
    
    antigate_key = os.environ[args.antigate]
    
    lor_registrator_result, lor_registrator_error = safe_run.safe_run(
            lor_registrator.lor_registrator,
            antigate_key,
            )
    
    if lor_registrator_error is not None:
        print('error: {!r}: {}'.format(
                lor_registrator_error[0],
                lor_registrator_error[1],
                ), file=sys.stderr)
        exit(code=1)
    
    email, login, password = lor_registrator_result
    
    print('"{}","{}","{}"'.format(
            email.replace('"', '""'),
            login.replace('"', '""'),
            password.replace('"', '""'),
            ))
