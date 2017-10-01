import functools
import json
import os

from bgmi.config import ADMIN_TOKEN
from bgmi.constants import ACTION_ADD, ACTION_DELETE, ACTION_CAL, ACTION_SEARCH, ACTION_CONFIG, ACTION_DOWNLOAD
from bgmi.controllers import add, delete, search, cal, config
from bgmi.download import download_prepare
from bgmi.front.base import BaseHandler

ACTION_AUTH = 'auth'


def auth_(token=''):
    return {'status': 'success' if token == ADMIN_TOKEN else 'error'}


API_MAP_POST = {
    ACTION_ADD: add,
    ACTION_DELETE: delete,
    ACTION_SEARCH: search,
    ACTION_CONFIG: config,
    ACTION_DOWNLOAD: download_prepare,
    ACTION_AUTH: auth_,
}

API_MAP_GET = {
    ACTION_CAL: lambda: {'data': cal()},
    ACTION_CONFIG: lambda: config(None, None)
}

NO_AUTH_ACTION = (ACTION_SEARCH, ACTION_CAL, ACTION_AUTH)


def auth(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if kwargs.get('action', None) in NO_AUTH_ACTION:
            return f(*args, **kwargs)

        token = args[0].request.headers.get('bgmi-token')
        if token == ADMIN_TOKEN:
            return f(*args, **kwargs)
        else:
            # yes,you are right
            args[0].set_status(401)
            args[0].write(args[0].jsonify(message='need auth', status='error'))

    return wrapper


class AdminApiHandler(BaseHandler):

    @auth
    def get(self, action, *args, **kwargs):
        if action in API_MAP_GET:
            if os.environ.get('DEV', False):
                self._add_header()
            self.finish(self.jsonify(**API_MAP_GET.get(action)()))

    @auth
    def post(self, action, *args, **kwargs):
        try:
            data = json.loads(self.request.body.decode('utf-8'))
            # self.add_header('content-type', 'application/json; charset=utf-8')

            if action in API_MAP_POST:
                if os.environ.get('DEV', False):
                    self._add_header()

                data = API_MAP_POST.get(action)(**data)
                if data['status'] == 'error':
                    self.set_status(400)
                    # self.finish(self.jsonify(message='bad request', status='error'))
                # else:
                data = self.jsonify(**data)
                self.finish(data)
            else:
                self.write_error(404)
                self.finish(self.jsonify(message='bad request', status='error'))

        except json.JSONEncoder:
            self.write_error(400)
