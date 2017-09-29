# coding: utf-8
from __future__ import print_function, unicode_literals

import os
import datetime
import json

from collections import OrderedDict

import tornado.escape

from bgmi import __version__
from bgmi.config import SAVE_PATH, DB_PATH, DANMAKU_API_URL
from bgmi.front.base import BaseHandler, WEEK, COVER_URL

from bgmi.models import Bangumi, Followed, STATUS_NORMAL, STATUS_UPDATING, STATUS_END
from bgmi.utils import normalize_path


class BangumiPlayerHandler(BaseHandler):
    def get(self, bangumi_name):
        data = Followed(bangumi_name=bangumi_name)
        data.select_obj()

        bangumi_obj = Bangumi(name=bangumi_name)
        bangumi_obj.select_obj()

        if not data:
            for i in self.patch_list:
                if bangumi_name == i['bangumi_name']:
                    data = i
                    bangumi_obj.cover = i['cover']
                    break

        if not data:
            return self.write_error(404)

        episode_list = {}
        bangumi_path = os.path.join(SAVE_PATH, bangumi_name)
        for root, _, files in os.walk(bangumi_path):
            if not _ and files:
                _ = root.replace(bangumi_path, '').split(os.path.sep)
                base_path = root.replace(SAVE_PATH, '')
                if len(_) >= 2:
                    episode_path = root.replace(os.path.join(SAVE_PATH, bangumi_name), '')
                    if episode_path.split(os.path.sep)[1].isdigit():
                        episode = int(episode_path.split(os.path.sep)[1])
                    else:
                        continue
                else:
                    episode = -1

                for bangumi in files:
                    if bangumi.lower().endswith('.mp4'):
                        mp4_path = os.path.join(base_path, bangumi).replace(os.path.sep, '/')
                        mp4_path = os.path.join(os.path.dirname(mp4_path),
                                                tornado.escape.url_escape(os.path.basename(mp4_path)))
                        episode_list[episode] = {'path': mp4_path.replace(os.path.sep, '/')}
                        print(os.path.join(base_path, bangumi))
                        break

        if not episode_list:
            self.write('_(:3 There are nothing to play, please try again later.')
            self.finish()
        else:
            self.render('templates/dplayer.html', bangumi=episode_list, bangumi_name=bangumi_name,
                        bangumi_cover='{}/{}'.format(COVER_URL, normalize_path(bangumi_obj['cover'])),
                        DANMAKU_URL=DANMAKU_API_URL)


class MainHandler(BaseHandler):
    def get(self, type_=''):

        if not os.path.exists(DB_PATH):
            self.write('BGmi db file not found.')
            self.finish()
            return

        if type_ == 'calendar':
            calendar = Bangumi.get_all_bangumi()

            for i in self.patch_list:
                calendar[i['update_time'].lower()].append(i)

            def shift(seq, n):
                n %= len(seq)
                return seq[n:] + seq[:n]

            weekday_order = shift(WEEK, datetime.datetime.today().weekday())
            cal_ordered = OrderedDict()

            for week in weekday_order:
                cal_ordered[week] = calendar[week.lower()]

            self.write(json.dumps(cal_ordered))

        else:
            data = Followed.get_all_followed(STATUS_NORMAL, STATUS_UPDATING,
                                             order='followed.updated_time', desc=True)

            followed = list(map(lambda b: b['bangumi_name'], data))
            followed.extend(list(map(lambda b: b['bangumi_name'], self.patch_list)))

            data = Followed.get_all_followed(STATUS_NORMAL, STATUS_UPDATING if not type_ == 'old' else STATUS_END,
                                             order='followed.updated_time', desc=True)

            if type_ == 'index':
                data.extend(self.patch_list)
                data.sort(key=lambda _: _['updated_time'])

            data.reverse()
            self.write(json.dumps(data))

        self.finish()
