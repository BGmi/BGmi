# coding: utf-8
from __future__ import print_function, unicode_literals

import datetime
import os
from collections import defaultdict

from icalendar import Calendar, Event

from bgmi.config import SAVE_PATH
from bgmi.front.base import BaseHandler
from bgmi.models import Download, Bangumi, Followed, Bangumi


class BangumiHandler(BaseHandler):
    def get(self, _):
        if os.environ.get('DEV', False):
            with open(os.path.join(SAVE_PATH, _), 'rb') as f:
                self.write(f.read())
                self.finish()
        else:
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
                       '...\n</pre>' % (SAVE_PATH, SAVE_PATH)
                       )
            self.finish()


class RssHandler(BaseHandler):
    def get(self):
        data = Download.get_all_downloads()
        self.set_header('Content-Type', 'text/xml')
        self.render('templates/download.xml', data=data)


class CalendarHandler(BaseHandler):
    def get(self):
        type_ = self.get_argument('type', 0)

        cal = Calendar()
        cal.add('prodid', '-//BGmi Followed Bangumi Calendar//bangumi.ricterz.me//')
        cal.add('version', '2.0')

        data = Followed.get_all_followed()
        data.extend(self.patch_list)

        if type_ == 0:

            bangumi = defaultdict(list)
            [bangumi[Bangumi.week.index(i['update_time']) + 1].append(i['bangumi_name']) for i in data]

            weekday = datetime.datetime.now().weekday()
            for i, k in enumerate(range(weekday, weekday + 7)):
                if k % 7 in bangumi:
                    for v in bangumi[k % 7]:
                        event = Event()
                        event.add('summary', v)
                        event.add('dtstart', datetime.datetime.now().date() + datetime.timedelta(i - 1))
                        event.add('dtend', datetime.datetime.now().date() + datetime.timedelta(i - 1))
                        cal.add_component(event)
        else:
            data = [bangumi for bangumi in data if bangumi['status'] == 2]
            for bangumi in data:
                event = Event()
                event.add('summary', 'Updated: {}'.format(bangumi['bangumi_name']))
                event.add('dtstart', datetime.datetime.now().date())
                event.add('dtend', datetime.datetime.now().date())
                cal.add_component(event)

        cal.add('name', 'Bangumi Calendar')
        cal.add('X-WR-CALNAM', 'Bangumi Calendar')
        cal.add('description', 'Followed Bangumi Calendar')
        cal.add('X-WR-CALDESC', 'Followed Bangumi Calendar')

        self.write(cal.to_ical())
        self.finish()


class NotFoundHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.set_status(404)
        self.write(self.jsonify(status='error', message='404 Not Found'))
        self.finish()

    def post(self, *args, **kwargs):
        self.get()

    def head(self, *args, **kwargs):
        self.get()
