# coding=utf-8
from __future__ import print_function, unicode_literals

import json
import re
import urllib
import datetime

import requests

from bgmi.config import IS_PYTHON3
from bgmi.script import ScriptBase
from bgmi.utils import print_error, parse_episode

if IS_PYTHON3:
    unquote = urllib.parse.unquote
else:
    unquote = urllib.unquote


class Script(ScriptBase):

    class Model(ScriptBase.Model):
        bangumi_name = '猜谜王(BGmi Script)'
        cover = 'COVER URL'
        update_time = 'Tue'
        due_date = datetime.datetime(2017, 9, 30)

    def get_download_url(self):
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
            ret[parse_episode(title)] = url

        return ret
