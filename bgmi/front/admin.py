import functools
import traceback
from concurrent.futures.thread import ThreadPoolExecutor
from threading import Lock
from typing import Any, Callable, Dict

from tornado.concurrent import run_on_executor
from tornado.ioloop import IOLoop
from tornado.web import HTTPError, RequestHandler

from bgmi.config import ADMIN_TOKEN
from bgmi.front.base import BaseHandler
from bgmi.lib.constants import (
    ACTION_ADD,
    ACTION_CAL,
    ACTION_CONFIG,
    ACTION_DELETE,
    ACTION_DOWNLOAD,
    ACTION_FILTER,
    ACTION_MARK,
    ACTION_SEARCH,
)
from bgmi.lib.controllers import (
    add,
    cal,
    config,
    delete,
    filter_,
    mark,
    search,
    status_,
    update,
)
from bgmi.lib.download import download_prepare

ACTION_AUTH = "auth"
ACTION_STATUS = "status"


def auth_(token: str = "") -> Dict[str, str]:
    return {"status": "success" if token == ADMIN_TOKEN else "error"}


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
}  # type: Dict[str, Callable]

API_MAP_GET = {
    ACTION_CAL: lambda: {"data": cal()},
    ACTION_CONFIG: lambda: config(None, None),
}

NO_AUTH_ACTION = (ACTION_CAL, ACTION_AUTH)


def auth(f):  # type: ignore
    @functools.wraps(f)
    def wrapped(self: RequestHandler, *args: Any, **kwargs: Any) -> Any:
        if kwargs.get("action", None) in NO_AUTH_ACTION:
            return f(self, *args, **kwargs)

        token = self.request.headers.get("bgmi-token")
        if token == ADMIN_TOKEN:
            return f(self, *args, **kwargs)
        else:
            # HTTPError will be except in `BaseHandler.write_error`
            raise HTTPError(401)

    return wrapped


class AdminApiHandler(BaseHandler):
    @auth
    def get(self, action: str) -> None:
        try:
            result = API_MAP_GET[action]()
        except KeyError:
            raise HTTPError(404)
        except Exception:
            traceback.print_exc()
            raise HTTPError(400)
        self.finish(self.jsonify(**result))

    @auth
    def post(self, action: str) -> None:
        data = self.get_json()

        try:
            result = API_MAP_POST[action](**data)
            if result["status"] == "error":
                raise HTTPError(400)
        except HTTPError:
            raise HTTPError(400)
        except KeyError:
            raise HTTPError(404)
        except Exception:
            traceback.print_exc()
            raise HTTPError(500)

        resp = self.jsonify(**result)
        self.finish(resp)


class UpdateHandler(BaseHandler):
    executor = ThreadPoolExecutor(2)
    lock = Lock()

    @auth
    async def post(self) -> None:
        if not self.lock.locked():
            self.lock.acquire()
            IOLoop.instance().add_callback(self.hard_task)  # 这样将在下一轮事件循环执行self.sleep
            await self.finish(self.jsonify(message="start updating"))
        else:
            await self.finish(self.jsonify(message="previous updating has not finish"))

    @run_on_executor
    def hard_task(self) -> None:
        print("start work")
        data = self.get_json()

        name = data.get("name", "")
        download = data.get("download", [])

        if not download:
            download = None
        update(name, download)
        self.lock.release()
