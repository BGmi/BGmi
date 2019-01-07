#!coding: utf-8
from __future__ import print_function, unicode_literals
import json
import json.decoder
import os

import tornado.web
from tornado.web import HTTPError

from bgmi import __version__, __admin_version__
from bgmi.config import DANMAKU_API_URL, BGMI_PATH, LANG
from bgmi.script import ScriptRunner
from bgmi.utils.utils import normalize_path

COVER_URL = '/bangumi/cover'
WEEK = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')


class BaseHandler(tornado.web.RequestHandler):
    patch_list = None
    latest_version = None

    def get_json(self):
        try:
            return json.loads(self.request.body.decode('utf-8'))
        except json.decoder.JSONDecodeError:
            raise HTTPError(400)

    def jsonify(self, data=None, **kwargs):
        j = {
            'version': __version__,
            'latest_version': self.latest_version,
            'frontend_version': __admin_version__,
            'status': 'success',
            'lang': LANG,
            'danmaku_api': DANMAKU_API_URL,
            'data': data
        }
        j.update(kwargs)
        self.set_header('content-type', 'application/json; charset=utf-8')
        return json.dumps(j, ensure_ascii=False, indent=2)

    def data_received(self, chunk):
        pass

    def __init__(self, *args, **kwargs):
        if self.latest_version is None:
            if os.path.exists(os.path.join(BGMI_PATH, 'latest')):
                with open(os.path.join(BGMI_PATH, 'latest')) as f:
                    self.latest_version = f.read().strip()

        if self.patch_list is None:
            runner = ScriptRunner()
            self.patch_list = runner.get_models_dict()
            for i in self.patch_list:
                i['cover'] = normalize_path(i['cover'])

        super(BaseHandler, self).__init__(*args, **kwargs)

    def write_error(self, status_code, **kwargs):
        """Override to implement custom error pages.

        ``write_error`` may call `write`, `render`, `set_header`, etc
        to produce output as usual.

        If this error was caused by an uncaught exception (including
        HTTPError), an ``exc_info`` triple will be available as
        ``kwargs["exc_info"]``.  Note that this exception may not be
        the "current" exception for purposes of methods like
        ``sys.exc_info()`` or ``traceback.format_exc``.
        """
        status_code = int(status_code)
        code_and_message_map = {
            400: 'Bad Request',
            401: 'Unauthorized Request',
            # 403: self._reason,
            404: '404 Not Found',
            405: '405 Method Not Allowed',
        }

        self.set_status(status_code)
        self.finish(self.jsonify(status='error',
                                 message=code_and_message_map.get(status_code, self._reason)))
