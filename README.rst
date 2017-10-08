BGmi
====
BGmi is a cli tool for subscribed bangumi.

|pypi|
|travis|
|coverage|

====
TODO
====
Empty as my wallet.

==========
Update Log
==========
+ Fully new frontend
+ Web page admin to config BGmi
+ Web page admin to add and delete bangumi
+ HTTP Api
+ Store bangumi cover image locally
+ Bangumi script support
+ Action source to select bangumi date source
+ Search / Download bangumi filter by regex
+ Download specified episode
+ Transmission-rpc support

=======
Feature
=======
+ Web page to subscribe bangumi
+ Bangumi Script: Write your bangumi parser own!
+ Bangumi data source: `bangumi_moe(default) <https://bangumi.moe>`_ or `mikan_project <https://mikanani.me>`_
+ Subscribe/unsubscribe bangumi
+ Bangumi calendar
+ Bangumi episode information
+ Download bangumi by subtitle group
+ Web page to view all subscribed bangumi
+ RSS feed for uTorrent
+ Play bangumi online with danmaku
+ Download bangumi by specified keywords (included and excluded).
+ **BGmi have supported Windows now**

.. image:: ./images/bgmi.png?raw=true
    :alt: BGmi
    :align: center
.. image:: ./images/bgmi_http.png?raw=true
    :alt: BGmi HTTP Service
    :align: center
.. image:: ./images/bgmi_player.png?raw=true
    :alt: BGmi HTTP Service
    :align: center

============
Installation
============
For **Mac OS X / Linux / Windows**:

.. code-block:: bash

    git clone https://github.com/BGmi/BGmi
    cd BGmi
    python setup.py install

Or use pip:

.. code-block:: bash

    pip install bgmi

.. code-block:: bash

    bgmi install # install BGmi-frontend


Build Docker:

.. code-block:: bash

    git clone https://github.com/BGmi/BGmi
    cd BGmi
    docker build -t bgmi .
    docker run -p8899:80 -d -v ~/.bgmi:/root/.bgmi bgmi

You can use bgmi command at client to add / remove bangumi, get into the docker container to manage bangumi.

Or just:

.. code-block:: bash

    docker pull ricterz/bgmi


=============
Usage of bgmi
=============

Supported data source:

**change data source will lose all bangumi you have followed!!**

bangumi you have downloaded will still store on the disk, but won't show on website

+ `bangumi_moe(default) <https://bangumi.moe>`_
+ `mikan_project <https://mikanani.me>`_
+ `dmhy <http://share.dmhy.org>`_

change to mikan by doing this

.. code-block:: bash

    bgmi source mikan_project
    bgmi cal

or change back:

.. code-block:: bash

    bgmi source bangumi_moe
    bgmi cal

Show bangumi calendar:

.. code-block:: bash

    bgmi cal


Subscribe bangumi:

.. code-block:: bash

    bgmi add "Re:CREATORS" "夏目友人帐 陆" "进击的巨人 season 2"
    bgmi add "樱花任务" --episode 0


Unsubscribe bangumi:

.. code-block:: bash

    bgmi delete --name "Re:CREATORS"


Update bangumi database which locates at ~/.bgmi/bangumi.db defaultly:

.. code-block:: bash

    bgmi update --download
    bgmi update "从零开始的魔法书" --download 2 3
    bgmi update "时钟机关之星" --download


Set up the bangumi subtitle group filter and fetch entries:

.. code-block:: bash

    bgmi list
    bgmi fetch "Re:CREATORS"
    bgmi filter "Re:CREATORS" --subtitle "DHR動研字幕組,豌豆字幕组" --include 720P --exclude BIG5
    bgmi fetch "Re:CREATORS"
    # remove subtitle, include and exclude keyword filter and add regex filter
    bgmi filter "Re:CREATORS" --subtitle "" --include "" --exclude "" --regex
    bgmi filter "Re:CREATORS" --regex "(DHR動研字幕組|豌豆字幕组).*(720P)"
    bgmi fetch "Re:CREATORS"


Search bangumi and download:

.. code-block:: bash

    bgmi search '为美好的世界献上祝福！' --regex-filter '.*动漫国字幕组.*为美好的世界献上祝福！].*720P.*'
    # download
    bgmi search '为美好的世界献上祝福！' --regex-filter '.*合集.* --download


Modify bangumi episode:

.. code-block:: bash

    bgmi list
    bgmi mark "Re:CREATORS" 1


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
    bgmi config ARIA2_RPC_TOKEN 'token:token233'

Fields of configure file:

BGmi configure:

+ :code:`BANGUMI_MOE_URL`: url of bangumi.moe mirror
+ :code:`BGMI_SAVE_PATH`: bangumi saving path
+ :code:`DOWNLOAD_DELEGATE`: the ways of downloading bangumi (aria2-rpc, transmission-rpc, xunlei)
+ :code:`MAX_PAGE`: max page for fetching bangumi information
+ :code:`BGMI_TMP_PATH`: just a temporary path
+ :code:`DANMAKU_API_URL`: url of danmaku api
+ :code:`LANG`: language

Aria2-rpc configure:

+ :code:`ARIA2_RPC_URL`: aria2c deamon RPC url
+ :code:`ARIA2_RPC_TOKEN`: aria2c deamon RPC token("token:" for no token)

Xunlei configure:

+ :code:`XUNLEI_LX_PATH`: path of xunlei-lixian binary

Transmission-rpc configure:

+ :code:`TRANSMISSION_RPC_URL`: transmission rpc host
+ :code:`TRANSMISSION_RPC_PORT`: transmission rpc port


==============
Bangumi Script
==============

Bangumi Script is a script which you can write the bangumi parser own.
BGmi will load the script and call the method you write before the native functionality.

Bangumi Script Runner will catch the data you returned, update the database, and download the bangumi.
You only just write the parser and return the data.

Bangumi Script is located at :code:`BGMI_PATH/script`, inherited :code:`ScriptBase` class. There is a example:

.. code-block:: python

    # coding=utf-8
    from __future__ import print_function, unicode_literals

    import re
    import json
    import requests
    import urllib

    from bgmi.utils import parse_episode
    from bgmi.script import ScriptBase
    from bgmi.utils import print_error
    from bgmi.config import IS_PYTHON3


    if IS_PYTHON3:
        unquote = urllib.parse.unquote
    else:
        unquote = urllib.unquote


    class Script(ScriptBase):

        # 定义 Model, 此处 Model 为显示在 BGmi HTTP 以及其他地方的名称、封面及其它信息
        class Model(ScriptBase.Model):
            bangumi_name = '猜谜王(BGmi Script)' # 名称, 随意填写即可
            cover = 'COVER URL' # 封面的 URL
            update_time = 'Tue' # 每周几更新

        def get_download_url(self):
            """Get the download url, and return a dict of episode and the url.
            Download url also can be magnet link.
            For example:
            ```
                {
                    1: 'http://example.com/Bangumi/1/1.mp4'
                    2: 'http://example.com/Bangumi/1/2.mp4'
                    3: 'http://example.com/Bangumi/1/3.mp4'
                }
            ```
            The keys `1`, `2`, `3` is the episode, the value is the url of bangumi.
            :return: dict
            """
            # fetch and return dict
            resp = requests.get('http://www.kirikiri.tv/?m=vod-play-id-4414-src-1-num-2.html').text
            data = re.findall("mac_url=unescape\('(.*)?'\)", resp)
            if not data:
                print_error('No data found, maybe the script is out-of-date.', exit_=False)
                return {}

            data = unquote(json.loads('["{}"]'.format(data[0].replace('%u', '\\u')))[0])

            ret = {}
            for i in data.split('#'):
                title, url = i.split('$')
                # parse_episode 为内置的解析集数的方法, 可以应对大多数情况。如若不可用, 可以自己实现解析
                ret[parse_episode(title)] = url

            return ret

Another example:

.. code-block:: python

    # coding=utf-8
    from __future__ import print_function, unicode_literals

    import re
    import requests
    from bs4 import BeautifulSoup as bs

    from bgmi.utils import parse_episode
    from bgmi.script import ScriptBase
    from bgmi.utils import print_error
    from bgmi.config import IS_PYTHON3


    class Script(ScriptBase):

        class Model(ScriptBase.Model):
            bangumi_name = 'Rick and Morty Season 3'
            cover = 'http://img.itvfans.com/wp-content/uploads/31346.jpg'
            update_time = 'Mon'

        def get_download_url(self):
            # fetch and return dict
            resp = requests.get('http://www.itvfans.com/fenji/313463.html').text
            html = bs(resp, 'lxml')

            data = html.find(attrs={'id': '31346-3-720p'})

            if not data:
                print_error('No data found, maybe the script is out-of-date.', exit_=False)
                return {}

            ret = {}
            match_episode = re.compile('Rick\.and\.Morty\.S03E(\d+)\.720p')
            for row in data.find_all('a', attrs={'type': 'magnet'}):
                link = row.attrs['href']
                episode = match_episode.findall(link)
                if episode:
                    ret[int(episode[0])] = link

            return ret


    if __name__ == '__main__':
        s = Script()
        print(s.get_download_url())


The returned dict as follows.

.. code-block:: bash

    {
        1: 'http://example.com/Bangumi/1/1.mp4'
        2: 'http://example.com/Bangumi/1/2.mp4'
        3: 'http://example.com/Bangumi/1/3.mp4'
    }

The keys `1`, `2`, `3` is the episode, the value is the url of bangumi.

==================
Usage of bgmi_http
==================

Start BGmi HTTP Service bind on :code:`0.0.0.0:8888`:

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
            # alias to BGMI_SAVE_PATH
            alias /var/www/html/bangumi;
        }

        location /admin {
            # alias to BGMI_ADMIN_PATH
            alias /var/www/html/admin;
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
        alias /var/www/html/yaaw;
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

First, setup nginx to access bangumi files.
Second, choose one danmaku backend at `DPlayer#related-projects <https://github.com/DIYgod/DPlayer#related-projects>`_.

Use `bgmi config` to setup the url of danmaku api.

.. code-block:: bash

    bgmi config DANMAKU_API_URL http://127.0.0.1:1207/

... and enjoy :D

=======
License
=======
The MIT License (MIT)

Copyright (c) 2017 Ricter Zheng

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


.. |pypi| image:: https://img.shields.io/pypi/v/bgmi.svg
   :target: https://pypi.python.org/pypi/bgmi

.. |travis| image:: https://travis-ci.org/BGmi/BGmi.svg?branch=master
   :target: https://travis-ci.org/BGmi/BGmi

.. |coverage| image:: https://codecov.io/gh/BGmi/BGmi/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/BGmi/BGmi