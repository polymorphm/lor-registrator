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

import os
import random
from urllib import parse as url_parse
from urllib import request as url_request
from http import cookiejar
import time
import json
import hashlib
import base64
import re
import html5lib
from . import et_find

TEMP_MAIL_ROOT_URL = 'http://api.temp-mail.ru/'
LOR_ROOT_URL = 'https://www.linux.org.ru/'
ANTIGATE_ROOT_URL = 'http://antigate.com/'
REQUEST_TIMEOUT = 60.0
REQUEST_READ_LIMIT = 10000000

class LorRegistratorError(Exception):
    pass

def gen_login():
    login_len = random.randrange(5, 11)
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

def lor_registrator(antigate_key):
    assert isinstance(antigate_key, str)
    
    cookies = cookiejar.CookieJar()
    opener = url_request.build_opener(
            url_request.HTTPCookieProcessor(cookiejar=cookies),
            )
    
    url = url_parse.urljoin(
            TEMP_MAIL_ROOT_URL,
            'request/domains/format/json/',
            )
    opener_res = opener.open(
            url_request.Request(url),
            timeout=REQUEST_TIMEOUT,
            )
    data = opener_res.read(REQUEST_READ_LIMIT).decode(errors='replace')
    email_domain_list = json.loads(data)
    
    if not isinstance(email_domain_list, (tuple, list)) or \
            not email_domain_list:
        raise LorRegistratorError(
                'no email_domain_list',
                )
    
    email_domain = random.choice(email_domain_list)
    
    if not isinstance(email_domain, str) or \
            not email_domain:
        raise LorRegistratorError(
                'no email_domain',
                )
    
    email_login = gen_login()
    email = email_login + email_domain
    login = gen_login()
    password = gen_login()
    
    url = url_parse.urljoin(LOR_ROOT_URL, 'register.jsp')
    opener_res = opener.open(
            url_request.Request(url),
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
    
    url = 'https://www.google.com/recaptcha/api/noscript?{}'.format(
            url_parse.urlencode({'k': recaptcha_k}),
            )
    opener_res = opener.open(
            url_request.Request(url),
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
    opener_res = opener.open(
            url_request.Request(url),
            timeout=REQUEST_TIMEOUT,
            )
    recaptcha_data = opener_res.read(REQUEST_READ_LIMIT)
    
    data = {
            'method': 'base64',
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
    opener_res = opener.open(
            url_request.Request(
                    url,
                    data=url_parse.urlencode(data).encode(errors='replace'),
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
    
    for att_i in range(20):
        time.sleep(5.0)
        
        email_md5 = hashlib.md5(email.encode(errors='replace')).hexdigest()
        url = url_parse.urljoin(
                TEMP_MAIL_ROOT_URL,
                'request/mail/id/{}/format/json/'.format(email_md5),
                )
        opener_res = opener.open(
                url_request.Request(url),
                timeout=REQUEST_TIMEOUT,
                )
        data = opener_res.read(REQUEST_READ_LIMIT).decode(errors='replace')
        mail_file_list = json.loads(data)
        
        if not isinstance(mail_file_list, (tuple, list)) or \
                not mail_file_list:
            continue
        
        for mail_file in mail_file_list:
            if not isinstance(mail_file, dict) or not mail_file:
                continue
            
            mail_from = mail_file.get('mail_from')
            
            if not isinstance(mail_from, str) or \
                    mail_from != 'no-reply@linux.org.ru':
                continue
            
            mail_text_only = mail_file.get('mail_text_only')
            
            if not isinstance(mail_text_only, str) or not mail_text_only:
                continue
            
            activate_key_prefix = 'Код активации: '
            key_match = re.search(
                    r'\s' + re.escape(activate_key_prefix) + r'(?P<code>\w+)\s',
                    mail_text_only,
                    flags=re.S,
                    )
            
            if key_match is None:
                continue
            
            activate_code = key_match.group('code')
            break
        else:
            continue
        
        break
    else:
        raise LorRegistratorError(
                'activate code not received',
                )
    
    data = {
            'csrf': csrf,
            'action': 'new',
            'nick': login,
            'passwd': password,
            'activation': activate_code,
            }
    url = url_parse.urljoin(LOR_ROOT_URL, 'activate.jsp')
    opener_res = opener.open(
            url_request.Request(
                    url,
                    data=url_parse.urlencode(data).encode(errors='replace'),
                    ),
            timeout=REQUEST_TIMEOUT,
            )
    data = opener_res.read(REQUEST_READ_LIMIT).decode(errors='replace')
    
    if opener_res.geturl() != LOR_ROOT_URL or not data:
        raise LorRegistratorError(
                'activation fail',
                )
    
    return email, login, password
