# coding: utf-8
import functools
import traceback
from concurrent.futures.thread import ThreadPoolExecutor
from tornado.ioloop import IOLoop

from tornado.concurrent import run_on_executor
from tornado.web import asynchronous, HTTPError

from bgmi.config import ADMIN_TOKEN
from bgmi.lib.constants import (ACTION_ADD, ACTION_DELETE, ACTION_CAL, ACTION_SEARCH, ACTION_CONFIG, ACTION_DOWNLOAD,
                                ACTION_MARK, ACTION_FILTER)
from bgmi.lib.controllers import add, delete, search, cal, config, update, mark, status_, filter_
from bgmi.lib.download import download_prepare
from bgmi.front.base import BaseHandler

ACTION_AUTH = 'auth'
ACTION_STATUS = 'status'


def auth_(token=''):
    return {'status': 'success' if token == ADMIN_TOKEN else 'error'}


API_MAP_POST = {
    ACTION_ADD: add,
    ACTION_DELETE: delete,
    ACTION_SEARCH: search,
    ACTION_CONFIG: config,
    ACTION_DOWNLOAD: download_prepare,
    ACTION_AUTH: auth_,
    ACTION_MARK: mark,
    ACTION_STATUS: status_,
    ACTION_FILTER: filter_,
}

API_MAP_GET = {
    ACTION_CAL: lambda: {'data': cal()},
    ACTION_CONFIG: lambda: config(None, None)
}

NO_AUTH_ACTION = (ACTION_CAL, ACTION_AUTH)


def auth(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if kwargs.get('action', None) in NO_AUTH_ACTION:
            return f(*args, **kwargs)

        token = args[0].request.headers.get('bgmi-token')
        if token == ADMIN_TOKEN:
            return f(*args, **kwargs)
        else:
            # HTTPError will be except in `BaseHandler.write_error`
            raise HTTPError(401)

    return wrapper


class AdminApiHandler(BaseHandler):
    @auth
    def get(self, action, *args, **kwargs):
        try:
            result = API_MAP_GET.get(action)()
        except Exception:
            traceback.print_exc()
            raise HTTPError(400)
        self.finish(self.jsonify(**result))

    @auth
    def post(self, action, *args, **kwargs):
        data = self.get_json()

        try:
            result = API_MAP_POST.get(action)(**data)
            if result['status'] == 'error':
                raise HTTPError(400)
        except HTTPError:
            raise HTTPError(400)
        except Exception:
            traceback.print_exc()
            raise HTTPError(500)

        resp = self.jsonify(**result)
        self.finish(resp)


# from tornado.locks import Lock
from threading import Lock


class UpdateHandler(BaseHandler):
    executor = ThreadPoolExecutor(2)
    lock = Lock()

    @auth
    @asynchronous
    def post(self):
        if not self.lock.locked():
            self.lock.acquire()
            IOLoop.instance().add_callback(self.hard_task)  # 这样将在下一轮事件循环执行self.sleep
            self.finish(self.jsonify(message='start updating'))
        else:
            self.finish(self.jsonify(message='previous updating has not finish'))

    @run_on_executor
    def hard_task(self, ):
        print('start work')
        data = self.get_json()

        name = data.get('name', '')
        download = data.get('download', [])

        if not download:
            download = None
        update(name, download)
        self.lock.release()
