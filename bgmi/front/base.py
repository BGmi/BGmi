import json

import tornado.web

from bgmi import __version__
from bgmi.config import DANMAKU_API_URL
from bgmi.script import ScriptRunner

COVER_URL = '/bangumi/cover'
WEEK = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')


class BaseHandler(tornado.web.RequestHandler):
    patch_list = None

    def jsonify(self, data=None, **kwargs):
        j = {
            'version': __version__,
            'status': 'success',
            'danmaku_api': DANMAKU_API_URL,
            'cover_url': COVER_URL,
            'data': data
        }
        j.update(kwargs)
        self.add_header('content-type', 'application/json; charset=utf-8')
        return json.dumps(j, ensure_ascii=False, indent=2)

    def data_received(self, chunk):
        pass

    def _add_header(self):
        self.add_header('Access-Control-Allow-Origin', 'http://localhost:8080')
        self.add_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.add_header("Access-Control-Allow-Headers",
                        "Content-Type,bgmi-token,bgmi-token, Access-Control-Allow-Headers, Authorization, X-Requested-With")

    def options(self, *args, **kwargs):
        self._add_header()
        self.finish('')

    def __init__(self, *args, **kwargs):
        if self.patch_list is None:
            runner = ScriptRunner()
            self.patch_list = runner.get_models_dict()

        super(BaseHandler, self).__init__(*args, **kwargs)
