# encoding: utf-8
from __future__ import print_function, unicode_literals

import os
import hashlib

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.template
import tornado.web
from tornado.options import options, define

from bgmi.front.admin import AdminApiHandler, AdminHandler
from bgmi.front.index import (MainHandler, ImageCSSHandler, BangumiPlayerHandler, BangumiHandler, RssHandler,
                              CalendarHandler)

define('port', default=8888, help='listen on the port', type=int)
define('address', default='0.0.0.0', help='binding at given address', type=str)


def md5(_, string):
    return hashlib.md5(string.encode('utf-8')).hexdigest()


def make_app():
    settings = {
        'static_path': os.path.join(os.path.dirname(__file__), 'static'),
        'ui_methods': [{'md5': md5}],
        'debug': True,
    }
    return tornado.web.Application([
        (r'/', MainHandler),
        (r'^/css/image.css$', ImageCSSHandler),
        (r'^/player/(.*)/$', BangumiPlayerHandler),
        (r'^/bangumi/(.*)', BangumiHandler),
        (r'^/rss$', RssHandler),
        (r'^/calendar.ics$', CalendarHandler),
        (r'^/api/?(?P<action>.*)', AdminApiHandler),
        (r'/admin/(.*)', AdminHandler)
    ], **settings)


def main():
    tornado.options.parse_command_line()
    print('BGmi HTTP Server listening on %s:%d' % (options.address, options.port))
    http_server = tornado.httpserver.HTTPServer(make_app())
    http_server.listen(options.port, address=options.address)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
