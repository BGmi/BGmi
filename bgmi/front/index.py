# coding: utf-8
from __future__ import print_function, unicode_literals

import datetime
import os
from collections import OrderedDict

from bgmi.config import SAVE_PATH, DB_PATH
from bgmi.front.base import BaseHandler, WEEK
from bgmi.models import Bangumi, Followed, STATUS_NORMAL, STATUS_UPDATING, STATUS_END


def get_player(bangumi_name):
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
                    mp4_path = os.path.join(base_path, bangumi)
                    mp4_path = os.path.join(os.path.dirname(mp4_path), os.path.basename(mp4_path))
                    mp4_path = mp4_path.replace(os.path.sep, '/')
                    episode_list[episode] = {'path': mp4_path}
                    break

    return episode_list


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

            self.write(self.jsonify(cal_ordered))

        else:
            data = Followed.get_all_followed(STATUS_NORMAL, STATUS_UPDATING,
                                             order='followed.updated_time', desc=True)

            followed = list(map(lambda b: b['bangumi_name'], data))
            followed.extend(list(map(lambda b: b['bangumi_name'], self.patch_list)))

            data = Followed.get_all_followed(STATUS_NORMAL, STATUS_UPDATING if not type_ == 'old' else STATUS_END,
                                             order='followed.updated_time', desc=True)

            if type_ == 'index':
                data.extend(self.patch_list)
                data.sort(key=lambda _: _['updated_time'] if _['updated_time'] else 1)

            data.reverse()

            for item in data:
                item['player'] = get_player(item['bangumi_name'])

            self.write(self.jsonify(data))

        self.finish()
