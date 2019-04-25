import json

from bgmi.script import ScriptBase


class Script(ScriptBase):
    class Model(ScriptBase.Model):
        bangumi_name = 'TEST_BANGUMI'
        cover = ''
        update_time = 'Mon'

    def get_download_url(self):
        # fetch and return dict
        resp = json.loads(
            '''{
  "1": "http://static.ricterz.me/",
  "2": "http://static.ricterz.me/",
  "3": "http://static.ricterz.me/",
  "4": "http://static.ricterz.me/"
}'''
        )

        ret = {}
        for k, v in resp.items():
            ret[int(k)] = v

        return ret


if __name__ == '__main__':  # pragma: no cover
    s = Script()
    s.get_download_url()
