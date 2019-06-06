import datetime
import os
from collections import defaultdict

from icalendar import Calendar, Event
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.web import HTTPError

from bgmi.config import SAVE_PATH
from bgmi.front.base import BaseHandler
from bgmi.lib.db_models import Bangumi, Download, Followed


class BangumiHandler(BaseHandler):
    def get(self, _):  # pylint: disable=W0221
        if os.environ.get('DEV', False):  # pragma: no cover
            with open(os.path.join(SAVE_PATH, _), 'rb') as f:
                self.write(f.read())
                self.finish()
        else:
            self.set_header('Content-Type', 'text/html')
            self.write('<h1>BGmi HTTP Service</h1>')
            self.write(
                '<pre>Please modify your web server configure file\n'
                'to server this path to \'%s\'.\n'
                'e.g.\n\n'
                '...\n'
                'autoindex on;\n'
                'location /bangumi {\n'
                '    alias %s;\n'
                '}\n'
                '...\n\n'
                'If use want to use Tornado to serve static files, please run\n'
                '<code>`bgmi config TORNADO_SERVE_STATIC_FILES 1`</code></pre>' %
                (SAVE_PATH, SAVE_PATH)
            )
            self.finish()


class RssHandler(BaseHandler):
    @gen.coroutine
    def get(self):  # pylint: disable=W0221
        data = yield from IOLoop.current().run_in_executor(None, Download.get_all_downloads, None)
        self.set_header('Content-Type', 'text/xml')
        self.render('templates/download.xml', data=data)


class CalendarHandler(BaseHandler):
    @gen.coroutine
    def get(self):  # pylint: disable=W0221
        type_ = self.get_argument('type', 0)

        cal = Calendar()
        cal.add('prodid', '-//BGmi Followed Bangumi Calendar//')
        cal.add('version', '2.0')
        cal.add('name', 'Bangumi Calendar')
        cal.add('X-WR-CALNAM', 'Bangumi Calendar')
        cal.add('description', 'Followed Bangumi Calendar')
        cal.add('X-WR-CALDESC', 'Followed Bangumi Calendar')

        data = yield IOLoop.current().run_in_executor(None, Followed.get_all_followed, None)
        data.extend(self.patch_list)

        if type_ == 0:

            bangumi = defaultdict(list)
            for i in data:
                bangumi[Bangumi.week.index(i['update_time']) + 1].append(i['bangumi_name'])

            weekday = datetime.datetime.now().weekday()
            for i, k in enumerate(range(weekday, weekday + 7)):
                if k % 7 in bangumi:
                    for v in bangumi[k % 7]:
                        event = Event()
                        event.add('summary', v)
                        event.add(
                            'dtstart',
                            datetime.datetime.now().date() + datetime.timedelta(i - 1),
                        )
                        event.add(
                            'dtend',
                            datetime.datetime.now().date() + datetime.timedelta(i - 1),
                        )
                        cal.add_component(event)
        else:
            data = [bangumi for bangumi in data if bangumi['status'] == 2]
            for bangumi in data:
                event = Event()
                event.add('summary', 'Updated: {}'.format(bangumi['bangumi_name']))
                event.add('dtstart', datetime.datetime.now().date())
                event.add('dtend', datetime.datetime.now().date())
                cal.add_component(event)

        if 'mozilla' not in self.request.headers.get('User-Agent', '').lower():
            # not browser, return icalendar
            self.set_header('content-type', 'text/calendar; charset=utf-8')
        else:
            # browser, show raw content
            self.set_header('content-type', 'text/plain; charset=utf-8')
        self.write(cal.to_ical())
        self.finish()


class NotFoundHandler(BaseHandler):
    def get(self, *args, **kwargs):
        raise HTTPError(404)
