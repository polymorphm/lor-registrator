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

import random
from urllib import parse as url_parse
from urllib import request as url_request
from http import cookiejar
import json
import random
import time
import base64
import re
import html5lib
import socket
import imaplib
from email import parser as email_parser
from . import et_find
from . import safe_run

try:
    from lib_socks_proxy_2013_10_03 import socks_proxy_context
except ImportError:
    socks_proxy_context = None

LOR_ROOT_URL = 'https://www.linux.org.ru/'
ANTIGATE_ROOT_URL = 'http://antigate.com/'
ANTIGATE_SOFT_ID = 585
REQUEST_TIMEOUT = 60.0
REQUEST_READ_LIMIT = 10000000

class LorRegistratorError(Exception):
    pass

class SafeIMAP4(imaplib.IMAP4):
    def _create_socket(self):
        sock = socket.create_connection(
                (self.host, self.port),
                timeout=15.0,
                )
        
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        
        return sock

def gen_login():
    login_len = random.randrange(7, 11)
    login_part_list = []
    
    is_next_vowel = False
    
    while len(login_part_list) < login_len:
        if is_next_vowel:
            next_part = random.choice((
                    'a', 'e', 'i', 'o', 'u',
                    ))
        else:
            next_part = random.choice((
                    'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm','n',
                    'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z',
                    ))
        is_next_vowel = not is_next_vowel
        login_part_list.append(next_part)
    
    return ''.join(login_part_list)

def get_useragent_list():
    url = 'https://getuseragent.blogspot.com/2014/03/getuseragent.html'
    marker_prefix = 'USERAGENT_DATA'
    start_marker = '{}_START'.format(marker_prefix)
    stop_marker = '{}_STOP'.format(marker_prefix)
    
    opener = url_request.build_opener()
    opener_res = opener.open(
            url_request.Request(url),
            timeout=REQUEST_TIMEOUT,
            )
    raw_data = opener_res.read(REQUEST_READ_LIMIT).decode(errors='replace')
    start_pos = raw_data.find(start_marker)
    stop_pos = raw_data.find(stop_marker)
    
    if start_pos == -1 or stop_pos == -1:
        raise ValueError(
                'not found: start_marker or stop_marker',
                )
    
    useragent_raw_data = raw_data[start_pos+len(start_marker):stop_pos]
    useragent_data = json.loads(useragent_raw_data)
    
    if not isinstance(useragent_data, (tuple, list)):
        raise ValueError(
                'useragent_data is not isinstance of tuple-or-list',
                )
    
    useragent_list = []
    
    for useragent_item in useragent_data:
        if not isinstance(useragent_item, str):
            continue
        
        useragent_list.append(useragent_item)
    
    return tuple(useragent_list)

def mail_fetch(email, imap_host, email_login, email_password):
    try:
        imap = SafeIMAP4(host=imap_host)
        try:
            imap.starttls()
            imap.login(email_login, email_password)
            imap.select()
            typ, search_data = imap.search(None, 'UNSEEN')
            
            for num in reversed(search_data[0].split()):
                typ, fetch_data = imap.fetch(num, '(RFC822)')
                
                msg_parser = email_parser.BytesFeedParser()
                msg_parser.feed(fetch_data[0][1])
                msg = msg_parser.close()
                
                msg_from = msg.get_all('from')
                msg_to = msg.get_all('to')
                msg_subject = msg.get_all('subject')
                
                if not msg_from or tuple(msg_from) != ('no-reply@linux.org.ru',) or \
                        not msg_to or tuple(msg_to) != (email,) or \
                        not msg_subject or tuple(msg_subject) != ('Linux.org.ru registration',):
                    continue
                
                for msg_part in msg.walk():
                    if msg_part.get_content_type() == 'text/plain':
                        payload = msg_part.get_payload(decode=True)
                        
                        assert isinstance(payload, bytes)
                        
                        msg_text = payload.decode(errors='replace')
                        
                        return msg_text
            
            imap.close()
        finally:
            imap.logout()
    except imaplib.IMAP4.error as imap_error:
        error_str = 'email is {!r}, error is {!r}'.format(
                email,
                imap_error,
                )
        raise imaplib.IMAP4.error(error_str)

def lor_open_phase(opener, open_func, useragent):
    url = url_parse.urljoin(LOR_ROOT_URL, 'register.jsp')
    opener_res = open_func(
            opener,
            url_request.Request(url, headers={'User-Agent': useragent}),
            timeout=REQUEST_TIMEOUT,
            )
    data = opener_res.read(REQUEST_READ_LIMIT).decode(errors='replace')
    doc = html5lib.parse(data)
    
    register_form_elem_list = tuple(et_find.find((doc,), (
            {'tag': '{http://www.w3.org/1999/xhtml}html'},
            {'tag': '{http://www.w3.org/1999/xhtml}body'},
            {
                    'tag': '{http://www.w3.org/1999/xhtml}form',
                    'attrib': {'action': 'register.jsp'},
                    },
            )))
    
    if not register_form_elem_list:
        raise LorRegistratorError(
                'no register_form_elem_list',
                )
    
    csrf_elem_list = tuple(et_find.find(register_form_elem_list, (
            {
                    'tag': '{http://www.w3.org/1999/xhtml}input',
                    'attrib': {'name': 'csrf'},
                    },
            )))
    
    if not csrf_elem_list:
        raise LorRegistratorError(
                'no csrf_elem_list',
                )
    
    script_elem_list = tuple(et_find.find(register_form_elem_list, (
            {
                    'tag': '{http://www.w3.org/1999/xhtml}script',
                    },
            )))
    
    if not script_elem_list:
        raise LorRegistratorError(
                'no script_elem_list',
                )
    
    csrf = csrf_elem_list[0].get('value')
    
    if not csrf:
        raise LorRegistratorError(
                'no csrf',
                )
    
    for script_elem in script_elem_list:
        script_url = script_elem.get('src')
        
        if not script_url:
            continue
        
        scheme, netloc, path, query, fragment = url_parse.urlsplit(script_url)
        
        if netloc != 'www.google.com' or \
                path != '/recaptcha/api/challenge' or \
                not query:
            continue
        
        query_map = url_parse.parse_qs(query)
        recaptcha_k_list = query_map.get('k')
        
        if not recaptcha_k_list:
            continue
        
        recaptcha_k = recaptcha_k_list[0]
        
        if not recaptcha_k:
            continue
        
        break
    else:
        raise LorRegistratorError(
                'no recaptcha_k',
                )
    
    return csrf, recaptcha_k

def get_recaptcha_phase(opener, open_func, useragent, recaptcha_k):
    url = 'https://www.google.com/recaptcha/api/noscript?{}'.format(
            url_parse.urlencode({'k': recaptcha_k}),
            )
    opener_res = open_func(
            opener,
            url_request.Request(url, headers={'User-Agent': useragent}),
            timeout=REQUEST_TIMEOUT,
            )
    data = opener_res.read(REQUEST_READ_LIMIT).decode(errors='replace')
    doc = html5lib.parse(data)
    
    recaptcha_form_elem_list = tuple(et_find.find((doc,), (
            {'tag': '{http://www.w3.org/1999/xhtml}html'},
            {'tag': '{http://www.w3.org/1999/xhtml}body'},
            {
                    'tag': '{http://www.w3.org/1999/xhtml}form',
                    'attrib': {'action': ''},
                    },
            )))
    
    if not recaptcha_form_elem_list:
        raise LorRegistratorError(
                'no recaptcha_form_elem_list',
                )
    
    recaptcha_challenge_elem_list = tuple(et_find.find(recaptcha_form_elem_list, (
            {
                    'tag': '{http://www.w3.org/1999/xhtml}input',
                    'attrib': {'name': 'recaptcha_challenge_field'},
                    },
            )))
    
    if not recaptcha_challenge_elem_list:
        raise LorRegistratorError(
                'no recaptcha_challenge_elem_list',
                )
    
    recaptcha_challenge = recaptcha_challenge_elem_list[0].get('value')
    
    if not recaptcha_challenge:
        raise LorRegistratorError(
                'no recaptcha_challenge',
                )
    
    url = 'https://www.google.com/recaptcha/api/image?{}'.format(
            url_parse.urlencode({'c': recaptcha_challenge}),
            )
    opener_res = open_func(
            opener,
            url_request.Request(url, headers={'User-Agent': useragent}),
            timeout=REQUEST_TIMEOUT,
            )
    recaptcha_data = opener_res.read(REQUEST_READ_LIMIT)
    
    return recaptcha_challenge, recaptcha_data

def antigate_phase(opener, antigate_key, recaptcha_data):
    data = {
            'method': 'base64',
            'soft_id': ANTIGATE_SOFT_ID,
            'key': antigate_key,
            'body': base64.b64encode(recaptcha_data),
            }
    url = url_parse.urljoin(ANTIGATE_ROOT_URL, 'in.php')
    opener_res = opener.open(
            url_request.Request(
                    url,
                    data=url_parse.urlencode(data).encode(errors='replace'),
                    ),
            timeout=REQUEST_TIMEOUT,
            )
    data = opener_res.read(REQUEST_READ_LIMIT).decode(errors='replace')
    
    if not data.startswith('OK|'):
        raise LorRegistratorError(
                'antigate error (when sening task): {}'.format(data),
                )
    
    antigate_task_id = data[len('OK|'):]
    
    while True:
        time.sleep(5.0)
        
        data = {
                'key': antigate_key,
                'action': 'get',
                'id': antigate_task_id,
                }
        url = url_parse.urljoin(
                ANTIGATE_ROOT_URL,
                'res.php?{}'.format(url_parse.urlencode(data)),
                )
        opener_res = opener.open(
                url_request.Request(url),
                timeout=REQUEST_TIMEOUT,
                )
        data = opener_res.read(REQUEST_READ_LIMIT).decode(errors='replace')
        
        if data == 'CAPCHA_NOT_READY':
            continue
        
        if not data.startswith('OK|'):
            raise LorRegistratorError(
                    'antigate error (when receiving task): {}'.format(data),
                    )
        
        recaptcha_response = data[len('OK|'):]
        break
    
    if not recaptcha_response:
        raise LorRegistratorError(
                'no recaptcha_response',
                )
    
    return recaptcha_response

def lor_register_phase(
        opener, open_func, useragent,
        csrf, recaptcha_challenge, recaptcha_response,
        email, login, password,
        ):
    data = {
            'csrf': csrf,
            'recaptcha_challenge_field': recaptcha_challenge,
            'recaptcha_response_field': recaptcha_response,
            'email': email,
            'nick': login,
            'password': password,
            'password2': password,
            'rules': 'okay',
            '_rules': 'on',
            }
    url = url_parse.urljoin(LOR_ROOT_URL, 'register.jsp')
    opener_res = open_func(
            opener,
            url_request.Request(
                    url,
                    data=url_parse.urlencode(data).encode(errors='replace'),
                    headers={'User-Agent': useragent},
                    ),
            timeout=REQUEST_TIMEOUT,
            )
    data = opener_res.read(REQUEST_READ_LIMIT).decode(errors='replace')
    doc = html5lib.parse(data)
    
    title_elem_list = tuple(et_find.find((doc,), (
            {'tag': '{http://www.w3.org/1999/xhtml}head'},
            {'tag': '{http://www.w3.org/1999/xhtml}title'},
            )))
    
    if not title_elem_list:
        raise LorRegistratorError(
                'no title_elem_list',
                )
    
    title = title_elem_list[0].text
    
    if title != 'Добавление пользователя прошло успешно. ' \
            'Ожидайте письма с кодом активации.':
        raise LorRegistratorError(
                'registration fail',
                )

def mail_phase(email, imap_host, email_login, email_password):
    for att_i in range(20):
        time.sleep(5.0)
        
        mail_text = mail_fetch(email, imap_host, email_login, email_password)
        
        if not mail_text:
            continue
        
        assert isinstance(mail_text, str)
        
        activate_key_prefix = 'Код активации: '
        key_match = re.search(
                r'\s' + re.escape(activate_key_prefix) + r'(?P<code>\w+)\s',
                mail_text,
                flags=re.S,
                )
        
        if key_match is None:
            continue
        
        activate_code = key_match.group('code')
        
        break
    else:
        raise LorRegistratorError(
                'activate code not received',
                )
    
    return activate_code

def lor_activate_phase(
        opener, open_func, useragent,
        csrf, login, password, activate_code,
        ):
    data = {
            'csrf': csrf,
            'action': 'new',
            'nick': login,
            'passwd': password,
            'activation': activate_code,
            }
    url = url_parse.urljoin(LOR_ROOT_URL, 'activate.jsp')
    opener_res = open_func(
            opener,
            url_request.Request(
                    url,
                    data=url_parse.urlencode(data).encode(errors='replace'),
                    headers={'User-Agent': useragent},
                    ),
            timeout=REQUEST_TIMEOUT,
            )
    data = opener_res.read(REQUEST_READ_LIMIT).decode(errors='replace')
    
    if opener_res.geturl() != LOR_ROOT_URL or not data:
        raise LorRegistratorError(
                'activation fail',
                )

def unsafe_lor_registrator(
        email, imap_host, email_login, email_password,
        antigate_key,
        proxy_address=None,
        ):
    assert isinstance(email, str)
    assert isinstance(imap_host, str)
    assert isinstance(email_login, str)
    assert isinstance(email_password, str)
    assert isinstance(antigate_key, str)
    
    if proxy_address is not None:
        # open via proxy
        
        def open_func(opener, *args, **kwargs):
            with socks_proxy_context.socks_proxy_context(proxy_address=proxy_address):
                return opener.open(*args, **kwargs)
    else:
        # default open action
        
        def open_func(opener, *args, **kwargs):
            return opener.open(*args, **kwargs)
    
    login = gen_login()
    password = gen_login()
    
    useragent_list = get_useragent_list()
    useragent = random.choice(useragent_list)
    
    cookies = cookiejar.CookieJar()
    opener = url_request.build_opener(
            url_request.HTTPCookieProcessor(cookiejar=cookies),
            )
    
    csrf, recaptcha_k = lor_open_phase(opener, open_func, useragent)
    recaptcha_challenge, recaptcha_data = get_recaptcha_phase(
            opener, open_func, useragent,
            recaptcha_k,
            )
    recaptcha_response = antigate_phase(opener, antigate_key, recaptcha_data)
    lor_register_phase(
            opener, open_func, useragent,
            csrf, recaptcha_challenge, recaptcha_response,
            email, login, password,
            )
    activate_code = mail_phase(email, imap_host, email_login, email_password)
    lor_activate_phase(
            opener, open_func, useragent,
            csrf, login, password, activate_code,
            )
    
    return email, login, password

def lor_registrator(*args, **kwargs):
    return safe_run.safe_run(unsafe_lor_registrator, *args, **kwargs)
