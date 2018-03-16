# coding=utf-8
from __future__ import print_function, unicode_literals
import requests
from bgmi.script import ScriptBase


class Script(ScriptBase):
    class Model(ScriptBase.Model):
        bangumi_name = 'TEST_BANGUMI'
        cover = ''
        update_time = 'Mon'

    def get_download_url(self):
        # fetch and return dict
        resp = requests.get('http://static.ricterz.me/bgmi_test.json').json()

        ret = {}
        for k, v in resp.items():
            ret[int(k)] = v

        return ret


if __name__ == '__main__':  # pragma: no cover
    s = Script()
    s.get_download_url()
