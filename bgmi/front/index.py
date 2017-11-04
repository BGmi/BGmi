# coding: utf-8
from __future__ import print_function, unicode_literals

import os

from bgmi.config import SAVE_PATH
from bgmi.front.base import BaseHandler, COVER_URL
from bgmi.models import STATUS_NORMAL, STATUS_UPDATING, STATUS_END, Followed
from bgmi.utils import normalize_path


def get_player(bangumi_name):
    episode_list = {}
    bangumi_path = os.path.join(SAVE_PATH, bangumi_name)
    for root, _, files in os.walk(bangumi_path):
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
            if any([bangumi.lower().endswith(x) for x in ['.mp4', '.mkv']]):
                video_file_path = os.path.join(base_path, bangumi)
                video_file_path = os.path.join(os.path.dirname(video_file_path), os.path.basename(video_file_path))
                video_file_path = video_file_path.replace(os.path.sep, '/')
                episode_list[episode] = {'path': video_file_path}
                break

    return episode_list


class MainHandler(BaseHandler):
    def get(self, type_=''):

        data = Followed.get_all_followed(STATUS_NORMAL, STATUS_UPDATING)

        followed = list(map(lambda b: b['bangumi_name'], data))
        followed.extend(list(map(lambda b: b['bangumi_name'], self.patch_list)))

        data = Followed.get_all_followed(STATUS_NORMAL, STATUS_UPDATING if not type_ == 'old' else STATUS_END)

        if type_ == 'index':
            data.extend(self.patch_list)
            data.sort(key=lambda _: _['updated_time'] if _['updated_time'] else 1)

        for bangumi in data:
            bangumi['cover'] = '{}/{}'.format(COVER_URL, normalize_path(bangumi['cover']))

        data.reverse()

        for item in data:
            item['player'] = get_player(item['bangumi_name'])

        self.write(self.jsonify(data))
        self.finish()
