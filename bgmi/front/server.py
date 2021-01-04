import asyncio
import sys
from itertools import chain
from typing import Any, List

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.routing
import tornado.template
import tornado.web
from tornado.options import define, options

from bgmi.config import (
    FRONT_STATIC_PATH,
    IS_WINDOWS,
    SAVE_PATH,
    TORNADO_SERVE_STATIC_FILES,
)
from bgmi.front.admin import API_MAP_GET, API_MAP_POST, AdminApiHandler, UpdateHandler
from bgmi.front.index import BangumiListHandler, IndexHandler
from bgmi.front.resources import BangumiHandler, CalendarHandler, RssHandler

define("port", default=8888, help="listen on the port", type=int)
define("address", default="0.0.0.0", help="binding at given address", type=str)


def make_app() -> tornado.web.Application:
    settings = {
        "autoreload": True,
        "gzip": True,
        "debug": True,
    }
    api_actions = "|".join(chain(API_MAP_GET.keys(), API_MAP_POST.keys()))

    handlers: List[Any] = [
        (r"^/api/(old|index)", BangumiListHandler),
        (r"^/resource/feed.xml$", RssHandler),
        (r"^/resource/calendar.ics$", CalendarHandler),
        (r"^/api/update", UpdateHandler),
        (fr"^/api/(?P<action>{api_actions})", AdminApiHandler),
    ]

    if TORNADO_SERVE_STATIC_FILES != "0":
        handlers.extend(
            [
                (r"/bangumi/(.*)", tornado.web.StaticFileHandler, {"path": SAVE_PATH}),
                (
                    r"^/(.*)$",
                    tornado.web.StaticFileHandler,
                    {"path": FRONT_STATIC_PATH, "default_filename": "index.html"},
                ),
            ]
        )
    else:
        handlers.extend(
            [
                (r"^/bangumi/?(.*)", BangumiHandler),
                (r"^/(.*)$", IndexHandler),
            ]
        )

    return tornado.web.Application(handlers, **settings)  # type: ignore


def main() -> None:
    if IS_WINDOWS:
        if sys.version_info >= (3, 8):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    tornado.options.parse_command_line()
    print(f"BGmi HTTP Server listening on {options.address}:{options.port:d}")
    http_server = tornado.httpserver.HTTPServer(make_app())
    http_server.listen(options.port, address=options.address)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
