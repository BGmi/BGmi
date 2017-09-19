import json

from tornado.web import RequestHandler

from bgmi.constants import ACTION_ADD, ACTION_DELETE, ACTION_CAL, ACTION_SEARCH, ACTION_CONFIG, ACTION_DOWNLOAD
from bgmi.controllers import add, delete, search, cal, config
from bgmi.download import download_prepare

api_map = {
    ACTION_ADD: add,
    ACTION_DELETE: delete,
    ACTION_CAL: cal,
    ACTION_SEARCH: search,
    ACTION_CONFIG: config,
    ACTION_DOWNLOAD: download_prepare
}


def jsonify(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2)


class ApiHandle(RequestHandler):
    def get(self, action, *args, **kwargs):
        if action in api_map:
            self.finish(jsonify(api_map.get(action)()))

    def post(self, action, *args, **kwargs):
        # print(self.request.body.decode('utf-8'))
        try:
            data = json.loads(self.request.body.decode('utf-8'))
            print(data)
            if action in api_map:
                self.finish(jsonify(api_map.get(action)(**data)))
        except json.JSONEncoder:
            self.write_error(502)
            return


    def options(self, *args, **kwargs):
        self.write('')
