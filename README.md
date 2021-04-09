# BGmi

BGmi is a cli tool for subscribed bangumi.

[中文说明](./README.cn.md)

[![pypi](https://img.shields.io/pypi/v/bgmi.svg)](https://pypi.python.org/pypi/bgmi) [![download](https://pepy.tech/badge/bgmi/month)](https://pepy.tech/project/bgmi) [![pipeline](https://dev.azure.com/BGmi/BGmi/_apis/build/status/BGmi.BGmi?branchName=master)](https://dev.azure.com/BGmi/BGmi/_apis/build/status/BGmi.BGmi?branchName=master) [![coverage](https://codecov.io/gh/BGmi/BGmi/branch/master/graph/badge.svg)](https://codecov.io/gh/BGmi/BGmi) [![license](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/BGmi/BGmi/blob/master/LICENSE)

## TODO

## Update Log

- New download delegate [qbittorrent-webapi](https://www.qbittorrent.org/)
- Remove python 3.5 support as it has reached its end-of-life
- Remove python 3.4 support as it has reached its end-of-life
- Remove Python2 support
- Transmission rpc authentication configuration
- New download delegate [deluge-rpc](https://www.deluge-torrent.org/)
- You can filter search results by min and max episode

more details can be found at [changelog.md](./changelog.md)

## Feature

- Multi data sources supported: [bangumi\_moe](https://bangumi.moe), [mikan\_project](https://mikanani.me) or [dmhy](https://share.dmhy.org/)
- Use aria2, transmission, deluge or qbittorrent to download bangumi
- Web interface to manage bangumi with HTTP API
- Play bangumi online with danmaku
- RSS feed for uTorrent, ICS calendar for mobile devices
- Bangumi Script: Write your own bangumi parser!
- Bangumi calendar / episode information
- Keyword, subtitle group, regular expression filters for download bangumi
- Windows, Linux and Router system supported, BGmi everywhere

![image](./images/bgmi_cli.png?raw=true%0A%20:alt:%20BGmi%0A%20:align:%20center)

![image](./images/bgmi_http.png?raw=true%0A%20:alt:%20BGmi%20HTTP%20Service%0A%20:align:%20center)

![image](./images/bgmi_player.png?raw=true%0A%20:alt:%20BGmi%20HTTP%20Service%0A%20:align:%20center)

![image](./images/bgmi_admin.png?raw=true%0A%20:alt:%20BGmi%20HTTP%20Service%0A%20:align:%20center)

## Installation

Using pip:

``` bash
pip install bgmi
```

Or from source(not recommended):

``` bash
git clone https://github.com/BGmi/BGmi
cd BGmi
python -m pip install -U pip
pip install .
```

Init BGmi database and install BGmi web interface:

``` bash
bgmi install
```

## Upgrade

``` bash
pip install bgmi -U
bgmi upgrade
```

Make sure to run bgmi upgrade after you upgrade your bgmi

## Docker

go to [BGmi/bgmi-docker-all-in-one](https://github.com/BGmi/bgmi-docker-all-in-one)

## Usage of bgmi

Cli completion(bash and zsh. Shell was detected from your env \$SHELL)

``` bash
eval "$(bgmi complete)"
```

If you want to setup a custom BGMI\_PATH instead of default `$HOME/.bgmi`:

``` bash
BGMI_PATH=/bgmi bgmi -h
```

Or add this code to your .bashrc file:

``` bash
alias bgmi='BGMI_PATH=/tmp bgmi'
```

Supported data source:

- [bangumi\_moe(default)](https://bangumi.moe)
- [mikan\_project](https://mikanani.me)
- [dmhy](https://share.dmhy.org/)

### Help

you can add `--help` to all `BGmi` sub command to show full options, some of them are not mentioned here.

### Change data source

**All bangumi info in database will be deleted when changing data source!** but scripts won't be affected

video files will still be stored on the disk, but won't be shown on website.

``` console
bgmi source mikan_project
```

### Show bangumi calendar

``` bash
bgmi cal
```

### Subscribe bangumi

``` bash
bgmi add "Re:CREATORS" "夏目友人帐 陆" "进击的巨人 season 2"
bgmi add "樱花任务" --episode 0
```

Default episode will be the latest episode.
If you just add a bangumi that you haven't watched any episodes, considering `bgmi add $BANGUMI_NAME --episode 0`.

### Unsubscribe bangumi

``` bash
bgmi delete --name "Re:CREATORS"
```

### Update bangumi

Update bangumi database (which locates at \~/.bgmi/bangumi.db acquiescently):

``` bash
bgmi update --download # download all undownloaded episode fo all followed bangumi
bgmi update "从零开始的魔法书" --download 2 3 # will download specific episide 2 and 3
bgmi update "时钟机关之星" --download # will download all undownloaded episode for specific bangumi
```

### Filter download

Set up the bangumi subtitle group filter and fetch entries:

``` bash
bgmi list
bgmi fetch "Re:CREATORS"
bgmi filter "Re:CREATORS" --subtitle "DHR動研字幕組,豌豆字幕组" --include 720P --exclude BIG5
bgmi fetch "Re:CREATORS"
# remove subtitle, include and exclude keyword filter and add regex filter
bgmi filter "Re:CREATORS" --subtitle "" --include "" --exclude ""
bgmi filter "Re:CREATORS" --regex "(DHR動研字幕組|豌豆字幕组).*(720P)"
bgmi fetch "Re:CREATORS"
```

### Search episodes

``` bash
bgmi search '为美好的世界献上祝福！' --regex-filter '.*动漫国字幕组.*为美好的世界献上祝福！.*720P.*'
# download
bgmi search '为美好的世界献上祝福！' --regex-filter '.*合集.*' --download
```

### Modify downloaded bangumi episode

``` bash
bgmi list
bgmi mark "Re:CREATORS" 1
```

This will tell bgmi to not need to download episode less than or equal to 1.

### Manage download items

``` bash
bgmi download --list
bgmi download --list --status 0
bgmi download --mark 1 --status 2
```

Status code:

- 0 - Not downloaded items
- 1 - Downloading items
- 2 - Downloaded items

### Show BGmi configure and modify it

``` bash
bgmi config
bgmi config ARIA2_RPC_TOKEN 'token:token233'
```

Fields of configure file:

BGmi configure:

- `BANGUMI_MOE_URL`: url of bangumi.moe mirror
- `SAVE_PATH`: bangumi saving path
- `DOWNLOAD_DELEGATE`: the ways of downloading bangumi (aria2-rpc, transmission-rpc, xunlei, deluge-rpc, qbittorrent-webapi)
- `MAX_PAGE`: max page for fetching bangumi information
- `TMP_PATH`: just a temporary path
- `DANMAKU_API_URL`: url of danmaku api
- `LANG`: language

Aria2-rpc configure:

- `ARIA2_RPC_URL`: aria2c daemon RPC url, not jsonrpc url.("<http://localhost:6800/rpc>" for localhost)
- `ARIA2_RPC_TOKEN`: aria2c daemon RPC token("token:" for no token)

Xunlei configure:

Xunlei-Lixian is deprecated, please choose aria2-rpc or transmission-rpc.

- `XUNLEI_LX_PATH`: path of xunlei-lixian binary

Transmission-rpc configure:

- `TRANSMISSION_RPC_URL`: transmission rpc host
- `TRANSMISSION_RPC_PORT`: transmission rpc port
- `TRANSMISSION_RPC_USERNAME`: transmission rpc username (leave it default if you don't set rpc authentication)
- `TRANSMISSION_RPC_PASSWORD`: transmission rpc password (leave it default if you don't set rpc authentication)

Deluge-rpc configure:

- `DELUGE_RPC_URL`: deluge rpc url
- `DELUGE_RPC_PASSWORD`: deluge rpc password

qbittorrent-webapi configure:

- `QBITTORRENT_HOST`: qbittorrent WebAPI host
- `QBITTORRENT_PORT`: qbittorrent WebAPI port
- `QBITTORRENT_USERNAME`: qbittorrent WebUI username
- `QBITTORRENT_PASSWORD`: qbittorrent WebUI password
- `QBITTORRENT_CATEGORY`: qbittorrent new task category (leave it default if you don't need to set category)

### Usage of bgmi\_http

Download all bangumi cover first:

``` bash
bgmi cal --download-cover
```

Download frontend static files(you may have done it before):

``` bash
bgmi install
```

Start BGmi HTTP Service bind on 0.0.0.0:8888:

``` bash
bgmi_http --port=8888 --address=0.0.0.0
```

### Use bgmi\_http on Windows

Just start your bgmi\_http and open [<http://localhost:8888/>](http://localhost:8888/) in your browser.

Consider most people won't use Nginx on Windows, bgmi\_http use tornado.web.StaticFileHandler to serve static files(frontend, bangumi covers, bangumi files) without Nginx.

### Use bgmi\_http on Linux

Generate Nginx config

``` bash
bgmi gen nginx.conf --server-name bgmi.whatever.com > bgmi.whatever.com
```

Or write your config file manually.

``` nginx
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
```

Of cause you can use [yaaw](https://github.com/binux/yaaw/) to manage download items if you use aria2c to download bangumi.

``` nginx
...
location /yaaw {
    alias /path/to/yaaw;
}

location /jsonrpc {
    # aria2c rpc
    proxy_pass http://127.0.0.1:6800;
}
...
```

Example file: [bgmi.conf](https://github.com/BGmi/BGmi/blob/dev/bgmi.conf)

#### DPlayer and Danmaku

BGmi use [DPlayer](https://github.com/DIYgod/DPlayer) to play bangumi.

First, setup nginx to access bangumi files. Second, choose one danmaku backend at [DPlayer\#related-projects](https://github.com/DIYgod/DPlayer#related-projects).

Use bgmi config to setup the url of danmaku api.

``` bash
bgmi config DANMAKU_API_URL https://api.prprpr.me/dplayer/ # This api is provided by dplayer official
```

...restart your bgmi\_http and enjoy :D

#### macOS launchctl service controller

see [issue \#77](https://github.com/BGmi/BGmi/pull/77)

[me.ricterz.bgmi.plist](https://github.com/BGmi/BGmi/blob/master/bgmi/others/me.ricterz.bgmi.plist)

## Bangumi Script

Bangumi Script is a script which you can write the bangumi parser own. BGmi will load the script and call the method you write before the native functionality.

Bangumi Script Runner will catch the data you returned, update the database, and download the bangumi. You only just write the parser and return the data.

Bangumi Script is located at BGMI\_PATH/script, inherited ScriptBase class.

examples: [script\_example.py](./script_example.py)

`get_download_url` returns a dict as follows.

``` python
{
    1: 'http://example.com/Bangumi/1/1.torrent',
    2: 'http://example.com/Bangumi/1/2.torrent',
    3: 'http://example.com/Bangumi/1/3.torrent'
}
```

The keys 1, 2, 3 is the episode, the value is the url of bangumi, make sure your download delegate support it..

## BGmi Data Source

You can easily add your own BGmi data source by extending BGmi website base class and implement all the method.

``` python
from typing import List, Optional

from bgmi.website.base import BaseWebsite
from bgmi.website.model import WebsiteBangumi, Episode


class DataSource(BaseWebsite):
    def search_by_keyword(
        self, keyword: str, count: int
    ) -> List[Episode]:  # pragma: no cover
        """

        :param keyword: search key word
        :param count: how many page to fetch from website
        :return: list of episode search result
        """
        raise NotImplementedError

    def fetch_bangumi_calendar(self,) -> List[WebsiteBangumi]:  # pragma: no cover
        """
        return a list of all bangumi and a list of all subtitle group

        list of bangumi dict:
        update time should be one of ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Unknown']
        """
        raise NotImplementedError

    def fetch_episode_of_bangumi(
        self, bangumi_id: str, max_page: int, subtitle_list: Optional[List[str]] = None
    ) -> List[Episode]:  # pragma: no cover
        """
        get all episode by bangumi id

        :param bangumi_id: bangumi_id
        :param subtitle_list: list of subtitle group
        :type subtitle_list: list
        :param max_page: how many page you want to crawl if there is no subtitle list
        :type max_page: int
        :return: list of bangumi
        """
        raise NotImplementedError


    def fetch_single_bangumi(self, bangumi_id: str) -> WebsiteBangumi:
        """
        fetch bangumi info when updating

        :param bangumi_id: bangumi_id, or bangumi['keyword']
        :type bangumi_id: str
        :rtype: WebsiteBangumi
        """
        # return WebsiteBangumi(keyword=bangumi_id) if website don't has a page contains episodes and info
```

## Debug

Set env BGMI\_LOG to debug, info, warning, error for different log level

log file will locate at {TMP\_PATH}/bgmi.log

## Uninstall

Scheduled task will not be delete automatically, you will have to remove them manually.

`*nix`:

remove them from your crontab

`windows`:

``` powershell
schtasks /Delete /TN 'bgmi updater'
```

## License

[MIT License](https://github.com/BGmi/BGmi/blob/master/LICENSE)
