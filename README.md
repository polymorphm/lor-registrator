lor-registrator
===============

``lor-registrator`` is utility for registration on web-site
``www.linux.org.ru`` with using ``antigate`` service.


Requirements
-------------

Utility requires module ``html5lib`` (``html5lib`` requires ``six``).


Status
------

Beta release lor-registrator-0.4.1 .


Using
-----

Example of using:

    $ ag_k='52453e4a874e3782b713980fa85358fe' ./lor-registrator.sh emails.csv ag_k

Out:

    "ibukimujiji+lor@yandex.ru","lizanemom","nanelima"
    "olypalin+lor@yandex.ru","ziwocuzuka","qozivahiba"
    "wuhowol+lor@yandex.ru","gokaqek","sogakiwimu"
    "nerawakihu+lor@yandex.ru","catuset","tetaros"
    error: <class 'imaplib.IMAP4.error'>: email is 'lakyqipe+lor@yandex.ru', error is error(b'[AUTHENTICATIONFAILED] LOGIN failure sc=ToVSFM5ZNqMO',)
    "honulazuf+lor@yandex.ru","riyecog","sipuhovuga"
    "bufybadob+lor@yandex.ru","gepufonoz","kefenefa"
    "hupapyvyw+lor@yandex.ru","wiyigusaxi","baqubab"
    "exuhaqyz+lor@yandex.ru","jinihecaza","vamolohe"
    "hejowinag+lor@yandex.ru","guzoluyivi","tupobuk"

The content of file ``emails.csv`` is:

    ibukimujiji+lor@yandex.ru,imap.yandex.com,ibukimujiji@yandex.ru,3o9WgePZ
    olypalin+lor@yandex.ru,imap.yandex.com,olypalin@yandex.ru,5DiWDiiU
    wuhowol+lor@yandex.ru,imap.yandex.com,wuhowol@yandex.ru,E-qLBQYUA
    nerawakihu+lor@yandex.ru,imap.yandex.com,nerawakihu@yandex.ru,psbeCK99
    lakyqipe+lor@yandex.ru,imap.yandex.com,lakyqipe@yandex.ru,4eC^LT&fa
    honulazuf+lor@yandex.ru,imap.yandex.com,honulazuf@yandex.ru,gTAojFay
    bufybadob+lor@yandex.ru,imap.yandex.com,bufybadob@yandex.ru,arIa2OfiMu
    hupapyvyw+lor@yandex.ru,imap.yandex.com,hupapyvyw@yandex.ru,nikolAS8
    exuhaqyz+lor@yandex.ru,imap.yandex.com,exuhaqyz@yandex.ru,2251975_
    hejowinag+lor@yandex.ru,imap.yandex.com,hejowinag@yandex.ru,QtJsGLCB

The content of file ``lor-registrator.sh`` is:

    #!/usr/bin/bash
    pkg_dir="$(dirname -- "$0")/site-packages"
    export PYTHONPATH="$pkg_dir/six-1.6.1:$pkg_dir/html5lib-0.999"
    exec -- "$(dirname -- "$0")/lor-registrator/lor-registrator" "$@"
    false

Example of using with proxy:

    $ sudo systemctl start tor
    $ ag_k='52453e4a874e3782b713980fa85358fe' ./lor-registrator.sh --proxy=127.0.0.1:9050 emails.csv ag_k
