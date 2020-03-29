import asyncio
import os
import sys

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.template
import tornado.web
from bgmi.config import (
    FRONT_STATIC_PATH,
    IS_WINDOWS,
    SAVE_PATH,
    TORNADO_SERVE_STATIC_FILES,
)
from bgmi.front.admin import API_MAP_GET, API_MAP_POST, AdminApiHandler, UpdateHandler
from bgmi.front.index import BangumiListHandler, IndexHandler
from bgmi.front.resources import BangumiHandler, CalendarHandler, RssHandler
from tornado.options import define, options

define('port', default=8888, help='listen on the port', type=int)
define('address', default='0.0.0.0', help='binding at given address', type=str)

API_ACTIONS = '{}|{}'.format('|'.join(API_MAP_GET.keys()), '|'.join(API_MAP_POST.keys()))

if os.environ.get('DEV'):  # pragma: no cover
    def prepare(self):
        self.set_header('Access-Control-Allow-Origin', 'http://localhost:8080')
        self.set_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.set_header("Access-Control-Allow-Headers",
                        "Content-Type, bgmi-token, X-Requested-With")


    tornado.web.RequestHandler.prepare = prepare


def make_app(**kwargs):
    settings = {
        'autoreload': True,
        'gzip': True,
        'debug': True,
    }
    settings.update(kwargs)
    handlers = [
        (r'^/api/(old|index)', BangumiListHandler),
        (r'^/resource/feed.xml$', RssHandler),
        (r'^/resource/calendar.ics$', CalendarHandler),
        (r'^/api/update', UpdateHandler),
        (r'^/api/(?P<action>%s)' % API_ACTIONS, AdminApiHandler),
    ]

    if TORNADO_SERVE_STATIC_FILES != '0':
        handlers.extend([
            (r'/bangumi/(.*)', tornado.web.StaticFileHandler, {'path': SAVE_PATH}),
            (r'^/(.*)$', tornado.web.StaticFileHandler, {'path': FRONT_STATIC_PATH,
                                                         'default_filename': 'index.html'})
        ])
    else:
        handlers.extend([
            (r'^/bangumi/?(.*)', BangumiHandler),
            (r'^/(.*)$', IndexHandler)
        ])

    return tornado.web.Application(handlers, **settings)


def main():
    if IS_WINDOWS:
        if sys.version_info[1] >= 8:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # print(tornado.options.options.__dict__)
    tornado.options.parse_command_line()
    print('BGmi HTTP Server listening on %s:%d' % (options.address, options.port))
    http_server = tornado.httpserver.HTTPServer(make_app())
    http_server.listen(options.port, address=options.address)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
