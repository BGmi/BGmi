import json
import tornado.web
from bgmi.script import ScriptRunner


COVER_URL = '/bangumi/cover'
WEEK = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')


def jsonify(obj):
    return json.dumps(obj, ensure_ascii=False)


class BaseHandler(tornado.web.RequestHandler):
    patch_list = None

    def data_received(self, chunk):
        pass

    def __init__(self, *args, **kwargs):
        if self.patch_list is None:
            runner = ScriptRunner()
            self.patch_list = runner.get_models_dict()

        super(BaseHandler, self).__init__(*args, **kwargs)
