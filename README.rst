BGmi
====
BGmi is a cli tool for subscribed bangumi.

`中文说明 <./README.cn.md>`_

|pypi|
|pypistats|
|travis|
|coverage|
|license|

====
TODO
====

==========
Update Log
==========
+ Fetch data from multi data sources at same time
+ Refactor server code to improve performance
+ Remove python2 support
+ Transmission rpc authentication configuration
+ New download delegate `deluge-rpc <https://www.deluge-torrent.org/>`_
+ You can filter search results by min and max episode

=======
Feature
=======
+ Multi data sources supported: `bangumi_moe <https://bangumi.moe>`_, `mikan_project <https://mikanani.me>`_ or `dmhy <https://share.dmhy.org/>`_
+ Use aria2, transmission or deluge to download bangumi
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

Attention: If you are using Python<3.6, please download a binary release with python3.6 interpreter

For **Mac OS X / Linux / Windows**:

Install from source:

.. code-block:: bash

    branch='master'
    pip install https://api.github.com/repos/BGmi/BGmi/tarball/$branch

Or use pip:

.. code-block:: bash

    pip install bgmi

If you want to use mysql as your database you need to install ``pymysql`` `<https://github.com/PyMySQL/PyMySQL>`_.

Or:

.. code-block:: bash

    pip install bgmi[mysql] # will use pymysql as driver

Init BGmi database and install BGmi web interface:

.. code-block:: bash

    bgmi install

if you don't need bgmi-frontend, add ``--no-web`` options to skip download front static file

** ``bgmi`` now will not try to create dirs and init db every time, you will have to use ``bgmi install`` at first time**

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
    # dev branch not working now
    git checkout dev
    docker build -t bgmi .

    alias bgmi='docker run -e BGMI_PATH=$HOME/.bgmi -v $HOME/.bgmi:$HOME/.bgmi --net host bgmi'
    alias bgmi_http='docker run -p 127.0.0.1:8888:8888 -e BGMI_PATH=$HOME/.bgmi -v $HOME/.bgmi:$HOME/.bgmi --net host bgmi'
    # bootstrap bgmi
    bgmi install
    # start bgmi http server in back ground
    bgmi_http


Make sure that docker env ``BGMI_PATH`` in docker is same as the path on host.
Because bgmi will tell downloader to download file in ``$BGMI_PATH/bangumi``.
So it must be same inside or outside the docker

Then use docker image as same as bgmi installed with pip:

.. code-block:: bash

    bgmi cal --download-cover

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


Show bangumi calendar:

.. code-block:: bash

    bgmi cal


Subscribe bangumi:

.. code-block:: bash

    bgmi add "Re:CREATORS" "夏目友人帐 陆" "进击的巨人 season 2"
    bgmi add "樱花任务" --episode 0


Unsubscribe bangumi:

.. code-block:: bash

    bgmi delete "Re:CREATORS"


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

Manually match bangumi from multi data source.

BGmi will try to find same bangumis from different data source.

`example <https://github.com/BGmi/BGmi/issues/109#issuecomment-435870748>`_

But there may also be accidents. like "魔偶马戏团" and "傀儡马戏团", so BGmi apply two actions for user to tell BGmi that
a bangumi name have different chinese translations.


.. code-block:: bash

    bgmi link 魔偶马戏团 傀儡马戏团
    bgmi cal --force-update

    bgmi unlink 魔偶马戏团 傀儡马戏团 # these two bangumis will be treated as different bangumis
    bgmi cal --force-update


Show BGmi configure and modify it:

.. code-block:: bash

    bgmi config
    bgmi config ARIA2_RPC_TOKEN 'token:token233'

Fields of configure file:

BGmi configure:

+ :code:`ENABLE_DATA_SOURCE`:enabled data sources.
+ :code:`BANGUMI_MOE_URL`: url of bangumi.moe mirror
+ :code:`BGMI_SAVE_PATH`: bangumi saving path
+ :code:`DOWNLOAD_DELEGATE`: the ways of downloading bangumi (aria2-rpc, transmission-rpc, deluge-rpc)
+ :code:`MAX_PAGE`: max page for fetching bangumi information
+ :code:`BGMI_TMP_PATH`: just a temporary path
+ :code:`DANMAKU_API_URL`: url of danmaku api
+ :code:`LANG`: language
+ :code:`DB_URL`: peewee Database URL, see `peewee#database-url <https://docs.peewee-orm.com/en/latest/peewee/playhouse.html#database-url>`_ for more details. Only sqlite and mysql are tested. default mysql database charset is :code:`utf8md4`, so if you are using mysql, you should set it you :code:`mysql://{username}:{password}@{host}:{port}/{dbname}?charset=utf8mb4`

Keyword Weight configure:

If you some preferred keywords like ``720``, ``内嵌`` or ``双语``,
but you don't want to include or exclude it,
you can add ``keyword=weight`` pair to ``keyword weight`` section of config file.

example:

.. code-block:: ini

    [keyword weight]
    720 = 10
    内嵌 = 100
    双语 = 100

If there are titles named ``720p 简体`` and ``1080p 双语`` and ``720 内嵌 双语``,
their weight will be ``10``, ``100`` and ``210``(``10+100+100``)
``bgmi`` will choose to download the third torrent.

Aria2-rpc configure:

+ :code:`ARIA2_RPC_URL`: aria2c daemon RPC url, not jsonrpc url.("http://localhost:6800/rpc" for localhost)
+ :code:`ARIA2_RPC_TOKEN`: aria2c daemon RPC token("token:" for no token)

Transmission-rpc configure:

+ :code:`TRANSMISSION_RPC_URL`: transmission rpc host
+ :code:`TRANSMISSION_RPC_PORT`: transmission rpc port
+ :code:`TRANSMISSION_RPC_USERNAME`: transmission rpc username (leave it default if you don't set rpc authentication)
+ :code:`TRANSMISSION_RPC_PASSWORD`: transmission rpc password (leave it default if you don't set rpc authentication)

Deluge-rpc configure:

+ :code:`DELUGE_RPC_URL`: deluge rpc url
+ :code:`DELUGE_RPC_PASSWORD`: deluge rpc password




==================
Usage of bgmi_http
==================
Download all bangumi cover:

.. code-block:: bash

    bgmi cal --download-cover

Download frontend static files:

.. code-block:: bash

    bgmi install

Start BGmi HTTP Service bind on :code:`0.0.0.0:8888`:

.. code-block:: bash

    bgmi_http --port=8888 --address=0.0.0.0

If you are using docker:

.. code-block:: bash

    host_port=8888
    aria2c_port=6800
    docker run -p127.0.0.1:$host_port:80 -p$aria2c_port:6800 -d -v $HOME/.bgmi:$HOME/.bgmi ricterz/bgmi

Behind a Web Server
-------------------
Generate a sample Nginx config

.. code-block:: bash

    bgmi gen nginx.conf --server-name bgmi.example.com

Generate a sample Caddyfile

.. code-block:: bash

    bgmi gen caddyfile --server-name bgmi.example.com

Generate systemd service unit file
----------------------------------

.. code-block:: bash

    bgmi gen bgmi_http.service | sudo tee /etc/systemd/system/bgmi_http.service
    sudo systemctl daemon-reload
    sudo systemctl enable bgmi_http.service
    sudo systemctl start bgmi_http.service


macOS launchctl service controller
----------------------------------
see `issue #77 <https://github.com/BGmi/BGmi/pull/77>`_

`me.ricterz.bgmi.plist <./bgmi/others/me.ricterz.bgmi.plist>`_

===================
DPlayer and Danmaku
===================

BGmi use `DPlayer <https://github.com/DIYgod/DPlayer>`_ to play bangumi.

First, setup your ``bgmi_http``.
Second, choose one danmaku backend at `DPlayer#related-projects <https://github.com/DIYgod/DPlayer#related-projects>`_.

Use ``bgmi config`` to setup the url of danmaku api.

.. code-block:: bash

    bgmi config DANMAKU_API_URL https://api.prprpr.me/dplayer/ # This api is provided by dplayer official, seems broken now.

...restart your :code:`bgmi_http` and enjoy :D

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

    import re
    import json
    import requests
    import urllib

    from bgmi.utils import parse_episode
    from bgmi.script import ScriptBase
    from bgmi.utils import print_error


    unquote = urllib.parse.unquote


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

    import re
    import requests
    from bs4 import BeautifulSoup as bs

    from bgmi.utils import parse_episode
    from bgmi.script import ScriptBase
    from bgmi.utils import print_error


    class Script(ScriptBase):

        class Model(ScriptBase.Model):
            bangumi_name = 'Rick and Morty Season 3'
            cover = 'http://img.itvfans.com/wp-content/uploads/31346.jpg'
            update_time = 'Mon'

        def get_download_url(self):
            # fetch and return dict
            resp = requests.get('http://www.itvfans.com/fenji/313463.html').text
            html = bs(resp, 'html.parser')

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

.. code-block:: python

    {
        1: 'http://example.com/Bangumi/1/1.mp4'
        2: 'http://example.com/Bangumi/1/2.torrent'
        3: 'magnet:?xt=urn:btih:aaa1bbb2ccc3ddd4eee5fff6ggg7'
    }


The keys ``1``, ``2``, ``3`` are the episodes, the values are the urls of bangumi files or torrent.

================
BGmi Data Source
================

You can easily add your own BGmi data source by extending BGmi website base(:code:`bgmi.website.base.BaseWebsite`) class and implement all the method.

.. code-block:: python
    from bgmi.website.base import BaseWebsite

    class DataSource(BaseWebsite)
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
                        "cover": "https://example.com/images/cover1.jpg"
                    },
                ]
            ```

            ``cover`` should be a full url of bangumi cover image file


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


===================
Debug
===================
Some error will not be raised unless you ``export DEBUG=1``.

Set env ``BGMI_LOG`` to ``debug``, ``info``, ``warning``, ``error`` for different log level

log file will locate at ``{TMP_PATH}/bgmi.log``

=========
Uninstall
=========
Scheduled task will not be delete automatically, you will have to remove them manually.

\*nix:

    remove them from your crontab

windows:

.. code-block:: bash

     schtasks /Delete /TN 'bgmi calendar updater'
     schtasks /Delete /TN 'bgmi bangumi updater'

Then, consider remove your ``~/.bgmi`` directory.

============
Contributing
============

`contributing.md <./.github/contributing.md>`_

=======
License
=======
The MIT License (MIT)

Copyright (c) 2017-2019 BGmi Developer Team (https://github.com/BGmi)

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

.. |travis| image:: https://img.shields.io/travis/BGmi/BGmi/master.svg
   :target: https://travis-ci.org/BGmi/BGmi

.. |coverage| image:: https://img.shields.io/codecov/c/github/BGmi/BGmi/master.svg
   :target: https://codecov.io/gh/BGmi/BGmi

.. |license| image:: https://img.shields.io/badge/License-MIT-blue.svg
   :target: https://github.com/BGmi/BGmi/blob/master/LICENSE

.. |pypistats| image::  https://img.shields.io/pypi/dm/bgmi.svg
   :target: https://pypi.python.org/pypi/bgmi
