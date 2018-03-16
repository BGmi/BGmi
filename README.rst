BGmi
====
BGmi is a cli tool for subscribed bangumi.

|pypi|
|travis|
|coverage|
|license|

====
TODO
====
Nothing here

==========
Update Log
==========
+ Fully new frontend

=======
Feature
=======
+ Multi data sources supported: `bangumi_moe <https://bangumi.moe>`_, `mikan_project <https://mikanani.me>`_ or `dmhy <https://share.dmhy.org/>`_
+ Use aria2, transmission or xunlei-lixian to download bangumi
+ Web interface to manage bangumi with HTTP API
+ Play bangumi online with danmaku
+ RSS feed for uTorrent, ICS calendar for mobile devices
+ Bangumi Script: Write your own bangumi parser!
+ Bangumi calendar / episode information
+ Keyword, subtitle group, regular expression filters for download bangumi
+ Windows, Linux and Router system supported, BGmi everywhere

.. image:: ./images/bgmi_cli.png?raw=true
    :alt: BGmi
    :align: center
.. image:: ./images/bgmi_http.png?raw=true
    :alt: BGmi HTTP Service
    :align: center
.. image:: ./images/bgmi_player.png?raw=true
    :alt: BGmi HTTP Service
    :align: center
.. image:: ./images/bgmi_admin.png?raw=true
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

Init BGmi database and install BGmi web interface:

.. code-block:: bash

    bgmi install

============
Upgrade
============
.. code-block:: bash

    pip install bgmi -U
    bgmi upgrade

Make sure to run :code:`bgmi upgrade` after you upgrade your bgmi

======
Docker
======
Build Docker:

.. code-block:: bash

    git clone https://github.com/BGmi/BGmi
    cd BGmi
    docker build -t bgmi .
    docker run -p127.0.0.1:8888:80 -p6800:6800 -d -v $HOME/.bgmi:$HOME/.bgmi bgmi

You can use bgmi command at client to add / remove bangumi, get into the docker container to manage bangumi.

Or just:

.. code-block:: bash

    docker pull ricterz/bgmi
    docker run -p127.0.0.1:8888:80 -p6800:6800 -d -v $HOME/.bgmi:$HOME/.bgmi ricterz/bgmi

Configure BGmi docker:

.. code-block:: bash

    # bgmi config ARIA2_RPC_TOKEN token:TOKEN_OF_ARIA2_RPC
    # docker exec -it <CONTAINER ID> ln -s ~/.bgmi/ /bgmi
    # docker exec -it <CONTAINER ID> bash -c 'echo rpc-secret=token:TOKEN_OF_ARIA2_RPC >> /root/aria2c.conf'
    # docker exec -it <CONTAINER ID> supervisorctl
    supervisor> restart bgmi:aria2c
    supervisor> quit

=============
Usage of bgmi
=============
Cli completion(bash and zsh. Shell was detected from your env $SHELL)

.. code-block:: bash

    eval "$(bgmi complete)"

Setup custom BGMI_PATH:

.. code-block:: bash

    BGMI_PATH=/bgmi bgmi -h

Or add this code to your .bashrc file:

.. code-block:: bash

    alias bgmi='BGMI_PATH=/tmp bgmi'

Supported data source:

+ `bangumi_moe(default) <https://bangumi.moe>`_
+ `mikan_project <https://mikanani.me>`_
+ `dmhy <https://share.dmhy.org/>`_

Change data source:

**All bangumi in database will be deleted when changing data source!** but scripts won't be affected

video files will still store on the disk, but won't be shown on website.


.. code-block:: bash

    bgmi source mikan_project

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


Update bangumi database which locates at ~/.bgmi/bangumi.db acquiescently:

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
    bgmi search '为美好的世界献上祝福！' --regex-filter '.*合集.*' --download


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

+ :code:`ARIA2_RPC_URL`: aria2c daemon RPC url, not jsonrpc url.("http://localhost:6800/rpc" for localhost)
+ :code:`ARIA2_RPC_TOKEN`: aria2c daemon RPC token("token:" for no token)

Xunlei configure:

XunleiLixian is deprecated, please choose aria2-rpc or transmission-rpc.

+ :code:`XUNLEI_LX_PATH`: path of xunlei-lixian binary

Transmission-rpc configure:

+ :code:`TRANSMISSION_RPC_URL`: transmission rpc host
+ :code:`TRANSMISSION_RPC_PORT`: transmission rpc port


==================
Usage of bgmi_http
==================
Download all bangumi cover:

.. code-block:: bash

    bgmi cal --download-cover

Download frontend static files(you may have done it before):

.. code-block:: bash

    bgmi install

Start BGmi HTTP Service bind on :code:`0.0.0.0:8888`:

.. code-block:: bash

    bgmi_http --port=8888 --address=0.0.0.0

Use bgmi_http on Windows
-----------------
Just start your bgmi_http and open `http://localhost:8888/ <http://localhost:8888/>`_ in your browser.

Consider most people won't use Nginx on Windows, bgmi_http use tornado.web.StaticFileHandler to serve static files(frontend, bangumi covers, bangumi files) without Nginx.

Use bgmi_http on Linux
-----------------
Configure tornado with Nginx:

.. code-block:: bash

    server {
        listen 80;
        server_name bgmi;

        root /path/to/bgmi;
        autoindex on;
        charset utf-8;

        location /bangumi {
            # ~/.bgmi/bangumi
            alias /path/to/bangumi;
        }

        location /api {
            proxy_pass http://127.0.0.1:8888;
            # Requests to api/update may take more than 60s
            proxy_connect_timeout 500s;
            proxy_read_timeout 500s;
            proxy_send_timeout 500s;
        }

        location /resource {
            proxy_pass http://127.0.0.1:8888;
        }

        location / {
            # ~/.bgmi/front_static/;
            alias /path/to/front_static/;
        }

    }

Of cause you can use `yaaw <https://github.com/binux/yaaw/>`_ to manage download items if you use aria2c to download bangumi.

.. code-block:: bash

    ...
    location /yaaw {
        alias /path/to/yaaw;
    }

    location /jsonrpc {
        # aria2c rpc
        proxy_pass http://127.0.0.1:6800;
    }
    ...

Example file: `bgmi.conf <https://github.com/BGmi/BGmi/blob/dev/bgmi.conf>`_

macOS launchctl service controller
-----------------
see `issue #77 <https://github.com/BGmi/BGmi/pull/77>`_

`me.ricterz.bgmi.plist <https://github.com/BGmi/BGmi/blob/master/bgmi/others/me.ricterz.bgmi.plist>`_

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

==============
Bangumi Script
==============

Bangumi Script is a script which you can write the bangumi parser own.
BGmi will load the script and call the method you write before the native functionality.

Bangumi Script Runner will catch the data you returned, update the database, and download the bangumi.
You only just write the parser and return the data.

Bangumi Script is located at :code:`BGMI_PATH/script`, inherited :code:`ScriptBase` class. There is an example:

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

================
BGmi Data Source
================
You can easily add your own BGmi data source by extending BGmi website base class and implement all the method.

.. code-block:: python

    class DataSource(bgmi.website.base.BaseWebsite)
        cover_url=''

        def search_by_keyword(self, keyword, count):
            """
            return a list of dict with at least 4 key: download, name, title, episode
            example:
            ```
                [
                    {
                        'name':"路人女主的养成方法",
                        'download': 'magnet:?xt=urn:btih:what ever',
                        'title': "[澄空学园] 路人女主的养成方法 第12话 MP4 720p  完",
                        'episode': 12
                    },
                ]

            :param keyword: search key word
            :type keyword: str
            :param count: how many page to fetch from website
            :type count: int

            :return: list of episode search result
            :rtype: list[dict]
            """
            raise NotImplementedError

        def fetch_bangumi_calendar_and_subtitle_group(self):
            """
            return a list of all bangumi and a list of all subtitle group

            list of bangumi dict:
            update time should be one of ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            example:
            ```
                [
                    {
                        "status": 0,
                        "subtitle_group": [
                            "123",
                            "456"
                        ],
                        "name": "名侦探柯南",
                        "keyword": "1234", #bangumi id
                        "update_time": "Sat",
                        "cover": "data/images/cover1.jpg"
                    },
                ]
            ```
            when downloading cover images, BGmi will try to get `self.cover_url + bangumi['cover']`


            list of subtitle group dict:
            example:
            ```
                [
                    {
                        'id': '233',
                        'name': 'bgmi字幕组'
                    }
                ]
            ```


            :return: list of bangumi, list of subtitile group
            :rtype: (list[dict], list[dict])
            """
            raise NotImplementedError

        def fetch_episode_of_bangumi(self, bangumi_id, subtitle_list=None, max_page=MAX_PAGE):
            """
            get all episode by bangumi id
            example
            ```
                [
                    {
                        "download": "magnet:?xt=urn:btih:e43b3b6b53dd9fd6af1199e112d3c7ff15cab82c",
                        "subtitle_group": "58a9c1c9f5dc363606ab42ec",
                        "title": "【喵萌奶茶屋】★七月新番★[来自深渊/Made in Abyss][07][GB][720P]",
                        "episode": 0,
                        "time": 1503301292
                    },
                ]
            ```

            :param bangumi_id: bangumi_id
            :param subtitle_list: list of subtitle group
            :type subtitle_list: list
            :param max_page: how many page you want to crawl if there is no subtitle list
            :type max_page: int
            :return: list of bangumi
            :rtype: list[dict]
            """
            raise NotImplementedError


=======
License
=======
The MIT License (MIT)

Copyright (c) 2017 BGmi Developer Team (https://github.com/BGmi)

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

.. |license| image:: https://img.shields.io/badge/License-MIT-blue.svg
   :target: https://github.com/BGmi/BGmi/blob/master/LICENSE
