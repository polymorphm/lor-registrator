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
import csv
from . import lor_registrator

try:
    from lib_socks_proxy_2013_10_03 import socks_proxy_context
except ImportError:
    socks_proxy_context = None

def read_emails(path):
    with open(path, encoding='utf-8', newline='', errors='replace') as fd:
        reader = csv.reader(fd)
        for row in reader:
            if len(row) != 4:
                raise ValueError(
                        'invalid format of emails file',
                        )
            
            email, imap_host, email_login, email_password = row
            
            yield email, imap_host, email_login, email_password

def main():
    parser = argparse.ArgumentParser(
            description='utility for registration on web-site '
                    '``www.linux.org.ru`` with using ``antigate`` service.',
            )
    
    parser.add_argument(
            '--proxy',
            metavar='SOCKS5-PROXY-ADDR',
            help='address of SOCKS5-proxy in format ``host:post``',
            )
    parser.add_argument(
            'emails',
            metavar='EMAIL-LIST-FILE-PATH',
            help='path to file with email list in CSV-format: '
                    'email,imap_host,email_login,email_password',
            )
    parser.add_argument(
            'antigate',
            metavar='ANTIGATE-KEY-ENV',
            help='system environ variable name with antigate key',
            )
    
    args = parser.parse_args()
    
    if args.proxy is not None:
        if socks_proxy_context is None:
            print(
                    'argument error: can not use proxy without module ``lib_socks_proxy_2013_10_03``',
                    file=sys.stderr,
                    )
            exit(code=2)
        
        proxy_address_split = args.proxy.rsplit(sep=':', maxsplit=1)
        
        if len(proxy_address_split) != 2:
            print(
                    'argument error: invalid format of proxy address',
                    file=sys.stderr,
                    )
            exit(code=2)
        
        proxy_address = proxy_address_split[0], int(proxy_address_split[1])
    else:
        proxy_address = None
    
    if args.antigate not in os.environ:
        print(
                'argument error: variable {!r} not found in system environ'.format(
                        args.antigate,
                        ),
                file=sys.stderr,
                )
        exit(code=2)
    
    emails_path = args.emails
    antigate_key = os.environ[args.antigate]
    
    for email, imap_host, email_login, email_password in read_emails(emails_path):
        lor_registrator_result, lor_registrator_error = lor_registrator.lor_registrator(
                email, imap_host, email_login, email_password,
                antigate_key,
                proxy_address=proxy_address,
                )
        
        if lor_registrator_error is not None:
            print('error: {!r}: {}'.format(
                    lor_registrator_error[0],
                    lor_registrator_error[1],
                    ), file=sys.stderr)
            continue
        
        email, login, password = lor_registrator_result
        
        print('"{}","{}","{}"'.format(
                email.replace('"', '""'),
                login.replace('"', '""'),
                password.replace('"', '""'),
                ))
