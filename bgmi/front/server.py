# encoding: utf-8
from __future__ import print_function, unicode_literals

import os

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.template
import tornado.web
from tornado.options import options, define

from bgmi.config import SAVE_PATH, FRONT_STATIC_PATH, IS_WINDOWS
from bgmi.front.admin import AdminApiHandler, UpdateHandler, API_MAP_POST, API_MAP_GET
from bgmi.front.base import BaseHandler
from bgmi.front.index import MainHandler
from bgmi.front.resources import RssHandler, CalendarHandler, NotFoundHandler, BangumiHandler

define('port', default=8888, help='listen on the port', type=int)
define('address', default='0.0.0.0', help='binding at given address', type=str)

API_ACTIONS = '%s|%s' % ('|'.join(API_MAP_GET.keys()), '|'.join(API_MAP_POST.keys()))

if os.environ.get('DEV'):  # pragma: no cover
    def prepare(self):
        self.set_header('Access-Control-Allow-Origin', 'http://localhost:8080')
        self.set_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, bgmi-token, X-Requested-With")


    tornado.web.RequestHandler.prepare = prepare


def make_app(**kwargs):
    settings = {
        'gzip': True,
        'debug': True,
    }
    settings.update(kwargs)
    handlers = [
        (r'^/api/(old|index)', MainHandler),
        (r'^/bangumi/?(.*)', BangumiHandler),
        (r'^/resource/feed.xml$', RssHandler),
        (r'^/resource/calendar.ics$', CalendarHandler),
        (r'^/api/update', UpdateHandler),
        (r'^/api/(?P<action>%s)' % API_ACTIONS, AdminApiHandler),
        (r'^/(.*)', NotFoundHandler)
    ]

    # if IS_WINDOWS:
    #     handlers[1] = (r'^/bangumi/(.*)', tornado.web.StaticFileHandler,
    #                    {'path': SAVE_PATH})
    #     handlers[6] = (r'^/(.*)', tornado.web.StaticFileHandler,
    #                    {'path': FRONT_STATIC_PATH,
    #                     "default_filename": "index.html"})

    return tornado.web.Application(handlers, **settings)


def main():
    tornado.options.parse_command_line()
    print('BGmi HTTP Server listening on %s:%d' % (options.address, options.port))
    http_server = tornado.httpserver.HTTPServer(make_app())
    http_server.listen(options.port, address=options.address)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
