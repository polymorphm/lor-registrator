lor-registrator
===============

``lor-registrator`` is utility for registration on web-site
``www.linux.org.ru`` with using ``antigate`` service.


Requirements
-------------

Utility requires module ``html5lib`` (``html5lib`` requires ``six``).


Status
------

Beta release version 0.2.2 .


Using
-----

Example of using:

$ ag_k='52453e4a874e3782b713980fa85358fe' ./lor-registrator.sh ag_k

    "cojon@solvemail.info","kidin","kihulunawa"

$ cat lor-registrator.sh

    #!/usr/bin/bash
    pkg_dir="$(dirname -- "$0")/site-packages"
    export PYTHONPATH="$pkg_dir/six-1.6.1:$pkg_dir/html5lib-0.999"
    exec -- "$(dirname -- "$0")/lor-registrator/lor-registrator" "$@"
    false
