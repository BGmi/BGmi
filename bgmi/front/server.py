import sys

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.template
import tornado.web
from tornado.options import define, options

from bgmi.config import FRONT_STATIC_PATH, SAVE_PATH, TORNADO_SERVE_STATIC_FILES
from bgmi.front.admin import API_MAP_GET, API_MAP_POST, AdminApiHandler, UpdateHandler
from bgmi.front.index import BangumiListHandler, IndexHandler
from bgmi.front.resources import BangumiHandler, CalendarHandler, RssHandler

API_ACTIONS = '{}|{}'.format('|'.join(API_MAP_GET.keys()), '|'.join(API_MAP_POST.keys()))


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
            (
                r'^/(.*)$', tornado.web.StaticFileHandler, {
                    'path': FRONT_STATIC_PATH, 'default_filename': 'index.html'
                }
            ),
        ])
    else:
        handlers.extend([
            (r'^/bangumi/?(.*)', BangumiHandler),
            (r'^/.*$', IndexHandler),
        ])

    return tornado.web.Application(handlers, **settings)


def main(args=None):
    define('port', default=8888, help='listen on the port', type=int)
    define('address', default='0.0.0.0', help='binding at given address', type=str)
    tornado.options.parse_command_line(args or sys.argv)
    http_server = tornado.httpserver.HTTPServer(make_app())
    http_server.listen(options.port, address=options.address)
    print('BGmi HTTP Server listening on http://%s:%d' % (options.address, options.port))
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
