BGmi
====
BGmi is a cli tool for subscribed bangumi.

|travis|
|pypi|

====
TODO
====
Empty as my wallet.

==========
Update Log
==========
+ Use argparse to parser command line arguments.

=======
Feature
=======
+ Subscribe/unsubscribe bangumi
+ Bangumi calendar
+ Bangumi episode informatdon
+ Download bangumi by subtitle group
+ Web page to view all subscribed bangumi
+ RSS feed for uTorrent
+ Play bangumi online with danmaku
+ Download bangumi by specified keywords (included and excluded).
+ **BGmi have supported Windows now**

.. image:: https://raw.githubusercontent.com/RicterZ/BGmi/master/images/bgmi.png
    :alt: BGmi
    :align: center
.. image:: https://raw.githubusercontent.com/RicterZ/BGmi/master/images/bgmi_http.png
    :alt: BGmi HTTP Service
    :align: center
.. image:: https://raw.githubusercontent.com/RicterZ/BGmi/master/images/bgmi_player.png
    :alt: BGmi HTTP Service
    :align: center

============
Installation
============
For **Mac OS X / Linux / Windows**:

.. code-block:: bash

    git clone https://github.com/RicterZ/BGmi
    cd BGmi
    python setup.py install

Or use pip:

.. code-block:: bash

    pip install bgmi

=============
Usage of bgmi
=============

Show bangumi calendar:

.. code-block:: bash

    bgmi cal all


Subscribe bangumi:

.. code-block:: bash

    bgmi add "Re：從零開始的異世界生活" "暗殺教室Ⅱ" "線上遊戲的老婆不可能是女生？" "在下坂本，有何貴幹？" "JoJo的奇妙冒險 不滅鑽石"


Unsubscribe bangumi:

.. code-block:: bash

    bgmi delete --name "暗殺教室Ⅱ"


Update bangumi database which locates at ~/.bgmi/bangumi.db defaultly:

.. code-block:: bash

    bgmi update --download
    bgmi update --name Rewrite 天真與閃電 --download


Set up the bangumi subtitle group filter and fetch entries:

.. code-block:: bash

    bgmi filter "線上遊戲的老婆不可能是女生？" --subtitle "KNA,惡魔島" --include 720p,720P --exclude BIG5
    bgmi fetch "線上遊戲的老婆不可能是女生？"
    # remove subtitle and exclude keyword filter
    bgmi filter "線上遊戲的老婆不可能是女生？" --subtitle "" --exclude ""
    bgmi fetch "線上遊戲的老婆不可能是女生？"


Modify bangumi episode:

.. code-block:: bash

    bgmi followed --list
    bgmi followed --mark Doraemon --episode 1


Manage download items:

.. code-block:: bash

    bgmi download --list
    bgmi download --list --status 0
    bgmi download --mark 1 --status 2

Status code:

+ 0 - Not downloaded items
+ 1 - Downloading items
+ 2 - Downloaded items

Show BGmi configure and modify it:

.. code-block:: bash

    bgmi config
    bgmi config --name MAX_PAGE --value 3

Fields of configure file:

+ :code:`DMHY_URL`: url of dmhy mirror
+ :code:`BGMI_SAVE_PATH`: bangumi saving path
+ :code:`DOWNLOAD_DELEGATE`: the ways of downloading bangumi (aria2, aria2-rpc, xunlei)
+ :code:`MAX_PAGE`: the max page of fetching bangumi info
+ :code:`BGMI_TMP_PATH`: just a temporary path
+ :code:`ARIA2_PATH`: the aria2c binary path
+ :code:`ARIA2_RPC_URL`: aria2c deamon RPC url
+ :code:`BGMI_LX_PATH`: path of xunlei-lixian binary
+ :code:`DANMAKU_API_URL`: url of danmaku api
+ :code:`CONVER_URL`: url of bangumi's cover

==================
Usage of bgmi_http
==================

Start BGmi HTTP Service bind on `0.0.0.0:8888`:

.. code-block:: bash

    bgmi_http --port=8888 --address=0.0.0.0

Configure tornado with nginx:

.. code-block:: bash

    server {
        listen 80;
        root /var/www/html/bangumi;
        autoindex on;
        charset utf8;
        server_name bangumi.example.com;

        location /bangumi {
            alias /var/www/html/bangumi;
        }

        location / {
            # reverse proxy to tornado listened port.
            proxy_pass http://127.0.0.1:8888;
        }
    }

Of cause you can use `yaaw <https://github.com/binux/yaaw/>`_ to manage download items if you use aria2c to download bangumi.

.. code-block:: bash

    ...
    location /bgmi_admin {
        auth_basic "BGmi admin (yaaw)";
        auth_basic_user_file /etc/nginx/htpasswd;
        alias /var/www/html/yaaw/;
    }

    location /jsonrpc {
        # aria2c listened port
        proxy_pass http://127.0.0.1:6800;
    }
    ...

===================
DPlayer and Danmaku
===================

BGmi use `DPlayer <https://github.com/DIYgod/DPlayer>`_ to play bangumi.

First, setup nginx to access bangumi files. Second, choose one danmaku backend at `DPlayer#related-projects <https://github.com/DIYgod/DPlayer#related-projects>`_.

Use `bgmi config` to setup the url of danmaku api.

.. code-block:: bash

    bgmi config DANMAKU_API_URL http://127.0.0.1:1207/

... and enjoy :D

=======
License
=======
The MIT License (MIT)

Copyright (c) 2016 Ricter Zheng

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

.. |travis| image:: https://travis-ci.org/RicterZ/BGmi.svg?branch=master
   :target: https://travis-ci.org/RicterZ/BGmi

.. |pypi| image:: https://img.shields.io/pypi/v/bgmi.svg
   :target: https://pypi.python.org/pypi/bgmi
