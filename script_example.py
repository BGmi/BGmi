import datetime
import json
import re
import urllib

import requests

from bgmi.script import ScriptBase
from bgmi.utils import parse_episode, print_error

unquote = urllib.parse.unquote


class Script(ScriptBase):
    class Model(ScriptBase.Model):
        bangumi_name = "猜谜王(BGmi Script)"
        cover = "COVER URL"
        update_time = "Tue"
        due_date = datetime.datetime(2017, 9, 30)

    def get_download_url(self):
        # fetch and return dict
        resp = requests.get(
            "http://www.kirikiri.tv/?m=vod-play-id-4414-src-1-num-2.html"
        ).text
        data = re.findall(r"mac_url=unescape\('(.*)?'\)", resp)
        if not data:
            print_error("No data found, maybe the script is out-of-date.", exit_=False)
            return {}

        data = unquote(json.loads('["{}"]'.format(data[0].replace("%u", "\\u")))[0])

        ret = {}
        for i in data.split("#"):
            title, url = i.split("$")
            ret[parse_episode(title)] = url

        return ret
