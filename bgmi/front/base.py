import json

import tornado.web

from bgmi import __version__, __admin_version__
from bgmi.config import DANMAKU_API_URL
from bgmi.script import ScriptRunner
from bgmi.utils.utils import normalize_path

COVER_URL = '/bangumi/cover'
WEEK = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')


class BaseHandler(tornado.web.RequestHandler):
    patch_list = None

    def _method_not_allowed(self):
        self.set_status(405)
        self.write(self.jsonify(status='error', message='405 Method Not Allowed'))
        self.finish()

    def options(self, *args, **kwargs):
        self.add_header('Access-Control-Allow-Origin', 'http://localhost:8080')
        self.add_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.add_header("Access-Control-Allow-Headers",
                        "Content-Type,bgmi-token,bgmi-token, "
                        "Access-Control-Allow-Headers, Authorization, X-Requested-With")

    def get(self, *args, **kwargs):
        self._method_not_allowed()

    def post(self, *args, **kwargs):
        self._method_not_allowed()

    def put(self, *args, **kwargs):
        self._method_not_allowed()

    def patch(self, *args, **kwargs):
        self._method_not_allowed()

    def delete(self, *args, **kwargs):
        self._method_not_allowed()

    def get_json(self):
        try:
            return json.loads(self.request.body.decode('utf-8'))
        except (json.JSONDecoder, ValueError):
            return {}

    def jsonify(self, data=None, **kwargs):
        j = {
            'version': __version__,
            'frontend_version': __admin_version__,
            'status': 'success',
            'danmaku_api': DANMAKU_API_URL,
            # 'cover_url': COVER_URL,
            'data': data
        }
        j.update(kwargs)
        self.set_header('content-type', 'application/json; charset=utf-8')
        return json.dumps(j, ensure_ascii=False, indent=2)

    def data_received(self, chunk):
        pass

    def __init__(self, *args, **kwargs):
        if self.patch_list is None:
            runner = ScriptRunner()
            self.patch_list = runner.get_models_dict()
            for i in self.patch_list:
                i['cover'] = normalize_path(i['cover'])

        super(BaseHandler, self).__init__(*args, **kwargs)
