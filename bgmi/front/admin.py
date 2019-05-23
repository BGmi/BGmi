# pylint: disable=W0221
import functools
import traceback
from concurrent.futures.thread import ThreadPoolExecutor
from threading import Lock

from playhouse.shortcuts import model_to_dict
from tornado.concurrent import run_on_executor
from tornado.ioloop import IOLoop
from tornado.web import HTTPError

from bgmi.config import ADMIN_TOKEN
from bgmi.front.base import BaseHandler
from bgmi.lib.constants.actions import (
    ACTION_ADD, ACTION_CAL, ACTION_DELETE, ACTION_DOWNLOAD, ACTION_FILTER, ACTION_MARK,
    ACTION_SEARCH
)
from bgmi.lib.controllers import add, cal, delete_, filter_, mark, search, status_, update
from bgmi.lib.download import download_prepare

ACTION_AUTH = 'auth'
ACTION_STATUS = 'status'


def auth_(token=''):
    return {'status': 'success' if token == ADMIN_TOKEN else 'error'}


def _filter(name, subtitle=None, include=None, exclude=None, regex=None):
    result = filter_(name, subtitle_input=subtitle, include=include, exclude=exclude, regex=regex)
    data = result.data
    data.update({
        'include': ', '.join(data['include'] or []),
        'exclude': ', '.join(data['exclude'] or []),
    })
    data['obj'] = model_to_dict(data['obj'])
    return {'status': result.status, 'data': result.data}


API_MAP_POST = {
    ACTION_ADD: add,
    ACTION_DELETE: delete_,
    ACTION_SEARCH: search,
    ACTION_DOWNLOAD: download_prepare,
    ACTION_AUTH: auth_,
    ACTION_MARK: mark,
    ACTION_STATUS: status_,
    ACTION_FILTER: _filter,
}

API_MAP_GET = {
    ACTION_CAL: lambda: {'data': cal()},
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
        # HTTPError will be except in `BaseHandler.write_error`
        raise HTTPError(401)

    return wrapper


class AdminApiHandler(BaseHandler):
    executor = ThreadPoolExecutor(4)

    @auth
    @run_on_executor
    def get(self, action):
        try:
            result = API_MAP_GET.get(action)()
        except Exception:
            traceback.print_exc()
            raise HTTPError(400)
        self.write(self.jsonify(**result))

    @auth
    @run_on_executor
    def post(self, action):
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

        resp = self.jsonify(
            status=result['status'],
            message=result.get('message'),
            data=result.get('data'),
        )
        self.write(resp)


class UpdateHandler(BaseHandler):
    executor = ThreadPoolExecutor(2)
    _lock = Lock()

    @auth
    def post(self):
        if self._lock.acquire(False):
            IOLoop.instance().add_callback(self.hard_task)  # 这样将在下一轮事件循环执行self.sleep
            self.finish(self.jsonify(message='start updating'))
        else:
            self.finish(self.jsonify(message='previous updating has not finish'))

    @run_on_executor
    def hard_task(self, ):
        data = self.get_json()

        name = data.get('name', '')
        download = data.get('download', [])

        if not download:
            download = None
        update(name, download)
        self._lock.release()
