import datetime
from typing import Dict

from bgmi.script import ScriptBase
from bgmi.utils import parse_episode


class Script(ScriptBase):
    class Model(ScriptBase.Model):
        bangumi_name = "TEST_BANGUMI"
        cover = ""
        update_time = "Mon"
        due_date = datetime.datetime(2080, 9, 30)

    def get_download_url(self) -> Dict[int, str]:
        # fetch and return dict
        resp = [
            {
                "title": "[YMDR][慕留人 -火影忍者新时代-][2017][2][AVC][JAP][BIG5][MP4][1080P]",
                "link": "http://example.com/Bangumi/1/2.torrent",
            },
            {
                "title": "[ZXSUB仲夏动漫字幕组][博人传-火影忍者次世代][03][720P繁体][MP4]",
                "link": "magnet:?xt=urn:btih:233",
            },
        ]

        ret = {}
        for item in resp:
            e = parse_episode(item["title"])
            if e:
                ret[e] = item["link"]

        return ret


if __name__ == "__main__":
    s = Script()
    print(s.get_download_url())
