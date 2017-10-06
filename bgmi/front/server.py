# encoding: utf-8
from __future__ import print_function, unicode_literals

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.template
import tornado.web
from tornado.options import options, define

from bgmi.front.admin import AdminApiHandler, UpdateHandler, API_MAP_POST, API_MAP_GET
from bgmi.front.index import MainHandler
from bgmi.front.resources import BangumiHandler, RssHandler, CalendarHandler, NotFoundHandler

define('port', default=8888, help='listen on the port', type=int)
define('address', default='0.0.0.0', help='binding at given address', type=str)


API_ACTIONS = '%s|%s' % ('|'.join(API_MAP_GET.keys()), '|'.join(API_MAP_POST.keys()))


def make_app(**kwargs):
    settings = {
        'debug': True,
    }
    settings.update(kwargs)
    return tornado.web.Application([
        (r'^/api/(old|index|calendar)', MainHandler),
        (r'^/bangumi/?(.*)', BangumiHandler),
        (r'^/resource/feed.xml$', RssHandler),
        (r'^/resource/calendar.ics$', CalendarHandler),
        (r'^/api/update', UpdateHandler),
        (r'^/api/?(?P<action>%s)' % API_ACTIONS, AdminApiHandler),
        (r'^/(.*)', NotFoundHandler)
    ], **settings)


def main():
    tornado.options.parse_command_line()
    print('BGmi HTTP Server listening on %s:%d' % (options.address, options.port))
    http_server = tornado.httpserver.HTTPServer(make_app())
    http_server.listen(options.port, address=options.address)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
