import json
import os

from bgmi.config import ADMIN_TOKEN
from bgmi.constants import ACTION_ADD, ACTION_DELETE, ACTION_CAL, ACTION_SEARCH, ACTION_CONFIG, ACTION_DOWNLOAD
from bgmi.controllers import add, delete, search, cal, config
from bgmi.download import download_prepare
from bgmi.front.http import BaseHandler


api_map_post = {
    ACTION_ADD: add,
    ACTION_DELETE: delete,
    ACTION_SEARCH: search,
    ACTION_CONFIG: config,
    ACTION_DOWNLOAD: download_prepare
}

api_map_get = {
    ACTION_CAL: cal,
    ACTION_CONFIG: lambda: config(None, None)
}


def jsonify(obj):
    return json.dumps(obj, ensure_ascii=False)


class ApiHandle(BaseHandler):
    def get(self, action, *args, **kwargs):
        if action in api_map_get:
            self.add_header('content-type', 'application/json; charset=utf-8')
            if os.environ.get('DEV', False):
                self.add_header('Access-Control-Allow-Origin', 'http://localhost:8080')
                self.add_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
                self.add_header("Access-Control-Allow-Headers",
                                "Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With")
            self.finish(jsonify(api_map_get.get(action)()))

    def post(self, action, *args, **kwargs):
        try:
            data = json.loads(self.request.body.decode('utf-8'))
            self.add_header('content-type', 'application/json; charset=utf-8')
            if action in api_map_post:
                if os.environ.get('DEV', False):
                    self.add_header('Access-Control-Allow-Origin', 'http://localhost:8080')
                    self.add_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
                    self.add_header("Access-Control-Allow-Headers",
                                    "Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With")
                data = api_map_post.get(action)(**data)
                if data['status'] == 'error':
                    self.set_status(502)
                data = jsonify(data)
                self.finish(data)
                return
            self.write_error(404)
            return
        except json.JSONEncoder:
            self.write_error(502)
            return

    def options(self, *args, **kwargs):
        self.add_header('Access-Control-Allow-Origin', 'http://localhost:8080')
        self.add_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.add_header("Access-Control-Allow-Headers",
                        "Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With")
        self.write('')
