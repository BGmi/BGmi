# encoding: utf-8
import os
import json
import datetime
import hashlib
import sqlite3
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.web
import tornado.template
from tornado.options import options, define
from collections import defaultdict, OrderedDict
from bgmi.config import BGMI_SAVE_PATH, DB_PATH


WEEK = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
define('port', default=8888, help='listen on the port', type=int)
define('address', default='0.0.0.0', help='binding at given address', type=str)


IMAGE_URL = 'http://bangumi.redrock-team.com'


def md5(_, string):
    return hashlib.md5(string.encode('utf-8')).hexdigest()


def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


class BangumiHandler(tornado.web.RequestHandler):
    def get(self, _):
        self.set_header('Content-Type', 'text/html')
        self.write('<h1>BGmi HTTP Service</h1>')
        self.write('<pre>Please modify your web server configure file\n'
                   'to server this path to \'%s\'.\n'
                   'e.g.\n\n'
                   '...\n'
                   'autoindex on;\n'
                   'location /bangumi {\n'
                   '    alias %s;\n'
                   '}\n'
                   '...\n</pre>' % (BGMI_SAVE_PATH, BGMI_SAVE_PATH)
                   )
        self.finish()


class ImageCSSHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = make_dicts
            cur = conn.cursor()
            cur.execute('SELECT bangumi_name FROM followed')
            data = cur.fetchall()
            cur.close()
            conn.close()

            self.set_header('Content-Type', 'text/css')
            self.render('templates/image.css', data=data, image_url=IMAGE_URL)
        except Exception, e:
            self.write(str(e))
            self.finish()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        is_json = self.get_argument('json', False)
        is_old = self.get_argument('old', False)

        if not os.path.exists(DB_PATH):
            self.write('BGmi db file not found.')
            self.finish()
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = make_dicts
            cur = conn.cursor()
            cur.execute('SELECT followed.* FROM followed LEFT JOIN '
                        'bangumi ON bangumi.name = followed.bangumi_name WHERE '
                        'followed.status != 0 and bangumi.status = %d'
                        ' ORDER BY followed.updated_time desc' % (1 if is_old else 0))
            data = cur.fetchall()
            cur.execute('SELECT name, update_time FROM bangumi WHERE bangumi.status = 0')
            calendar = cur.fetchall()
            cur.close()
            conn.close()

            def shift(seq, n):
                n = n % len(seq)
                return seq[n:] + seq[:n]

            cal = defaultdict(list)
            for row in calendar:
                cal[row['update_time']].append(row['name'])

            weekday_order = shift(WEEK, datetime.datetime.today().weekday())
            cal_ordered = OrderedDict()

            for week in weekday_order:
                cal_ordered[week] = cal[week]

            if is_json:
                self.write(json.dumps(cal_ordered))
                self.finish()
            else:
                self.render('templates/bangumi.html', data=data, cal=cal_ordered)
        except Exception, e:
            self.write(str(e))
            self.finish()


def make_app():
    settings = {
        'static_path': os.path.join(os.path.dirname(__file__), 'static'),
        'ui_methods': [{'md5': md5}],
        'debug': True,
    }
    return tornado.web.Application([
        (r'/', MainHandler),
        (r'/css/image.css', ImageCSSHandler),
        (r'/bangumi/(.*)', BangumiHandler),
    ], **settings)


def main():
    tornado.options.parse_command_line()
    print('BGmi HTTP Server listening on %s:%d' % (options.address, options.port))
    http_server = tornado.httpserver.HTTPServer(make_app())
    http_server.listen(options.port, address=options.address)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
