# coding=utf-8
from __future__ import print_function, unicode_literals

import datetime
import glob
import os
import re
import string
import time
from collections import defaultdict
from itertools import chain

import requests
import tqdm

import bgmi.config
from bgmi.config import MAX_PAGE
from bgmi.models import Bangumi, Filter, Subtitle, STATUS_FOLLOWED, STATUS_UPDATED
from bgmi.script import ScriptRunner
from bgmi.utils import (parse_episode, print_warning, print_info,
                        test_connection, get_terminal_col, GREEN, YELLOW, COLOR_END)

if bgmi.config.IS_PYTHON3:
    _unicode = str
else:
    _unicode = unicode


class BaseWebsite(object):
    parse_episode = staticmethod(parse_episode)
    def search(self, keyword='', count=1, filter_=None):
        if not filter_:
            filter_ = '(.*)'
        match_title = re.compile(filter_)
        result = self.raw_search(keyword, count)
        # filter
        filtered_result = []
        for episode in result:
            if match_title.match(episode['title']):
                filtered_result.append(episode)
        result = filtered_result[:]

        # remove duplicated episode in result
        ret = []
        episodes = list({i['episode'] for i in result})
        for i in result:
            if i['episode'] in episodes:
                ret.append(i)
                del episodes[episodes.index(i['episode'])]

        if os.environ.get('DEBUG', None):
            for i in ret:
                print(i['title'], i['download'])
        return ret

    def raw_search(self, keyword='', count=1, ):
        return self.search_by_keyword(keyword, count)

    @staticmethod
    def save_data(data):
        b = Bangumi(**data)
        b.save()

    def fetch(self, save=False, group_by_weekday=True, status=False):
        bangumi_result, subtitle_group_result = self.fetch_bangumi_calendar_and_subtitle_group()
        if subtitle_group_result:
            for subtitle_group in subtitle_group_result:
                s = Subtitle(id=_unicode(subtitle_group['id']), name=_unicode(subtitle_group['name']))
                if not s.select():
                    s.save()
        if not bangumi_result:
            print('no result return None')
            return []

        if save:
            for bangumi in bangumi_result:
                self.save_data(bangumi)
        if group_by_weekday:
            result_group_by_weekday = defaultdict(list)
            for bangumi in bangumi_result:
                result_group_by_weekday[bangumi['update_time'].lower()].append(bangumi)
            bangumi_result = result_group_by_weekday
        return bangumi_result

    def bangumi_calendar(self, force_update=False, today=False, followed=False, save=True):
        env_columns = get_terminal_col()

        col = 42

        if env_columns < col:
            print_warning('terminal window is too small.')
            env_columns = col

        row = int(env_columns / col if env_columns / col <= 3 else 3)

        if force_update and not test_connection():
            force_update = False
            print_warning('network is unreachable')

        if force_update:
            print_info('fetching bangumi info ...')
            Bangumi.delete_all()
            weekly_list = self.fetch(save=save, status=True)
        else:
            if followed:
                weekly_list_followed = Bangumi.get_all_bangumi(status=STATUS_FOLLOWED)
                weekly_list_updated = Bangumi.get_all_bangumi(status=STATUS_UPDATED)
                weekly_list = defaultdict(list)
                for k, v in chain(weekly_list_followed.items(), weekly_list_updated.items()):
                    weekly_list[k].extend(v)
            else:
                weekly_list = Bangumi.get_all_bangumi()
        init = False
        if not weekly_list:
            if not followed:
                init = True
                print_warning('warning: no bangumi schedule, fetching ...')
                weekly_list = self.fetch(save=save)
            else:
                print_warning('you have not subscribed any bangumi')

        def shift(seq, n):
            n %= len(seq)
            return seq[n:] + seq[:n]

        def print_line():
            num = col - 3
            split = '-' * num + '   '
            print(split * row)

        result = []
        if today:
            weekday_order = (Bangumi.week[datetime.datetime.today().weekday()],)
            result = shift(Bangumi.week, datetime.datetime.today().weekday())
        else:
            weekday_order = shift(Bangumi.week, datetime.datetime.today().weekday())
            result = weekly_list.copy()

        runner = ScriptRunner()
        patch_list = runner.get_models_dict()
        result = weekly_list.copy()
        for i in patch_list:
            weekly_list[i['update_time'].lower()].append(i)

        spacial_append_chars = ['Ⅱ', 'Ⅲ', '♪', 'Δ', '×', '☆', 'é', '·', '♭']
        spacial_remove_chars = []

        for index, weekday in enumerate(weekday_order):
            if weekly_list[weekday.lower()]:
                print('%s%s. %s' % (GREEN,
                                    weekday if not today else 'Bangumi Schedule for Today (%s)' % weekday, COLOR_END),
                      end='')
                if not followed:
                    print()
                    print_line()

                for i, bangumi in enumerate(weekly_list[weekday.lower()]):
                    if bangumi['status'] in (STATUS_UPDATED, STATUS_FOLLOWED) and 'episode' in bangumi:
                        bangumi['name'] = '%s(%d)' % (bangumi['name'], bangumi['episode'])

                    half = len(re.findall('[%s]' % string.printable, bangumi['name']))
                    full = (len(bangumi['name']) - half)
                    space_count = col - 2 - (full * 2 + half)

                    for s in spacial_append_chars:
                        if s in bangumi['name']:
                            space_count += 1

                    for s in spacial_remove_chars:
                        if s in bangumi['name']:
                            space_count -= 1

                    if bangumi['status'] == STATUS_FOLLOWED:
                        bangumi['name'] = '%s%s%s' % (YELLOW, bangumi['name'], COLOR_END)

                    if bangumi['status'] == STATUS_UPDATED:
                        bangumi['name'] = '%s%s%s' % (GREEN, bangumi['name'], COLOR_END)

                    if followed:
                        if i > 0:
                            print(' ' * 5, end='')
                        f = map(lambda x: x['name'], Subtitle.get_subtitle(bangumi['subtitle_group'].split(', ')))
                        print(bangumi['name'], ', '.join(f))
                    else:
                        print(' ' + bangumi['name'], ' ' * space_count, end='')
                        if (i + 1) % row == 0 or i + 1 == len(weekly_list[weekday.lower()]):
                            print()

                if not followed:
                    print()
        # for web api
        r = result.copy()
        for day, value in result.items():
            for index, bangumi in enumerate(value):
                if isinstance(bangumi['subtitle_group'], list):
                    subtitle_group = list(map(lambda x: {'name': x['name'], 'id': x['id']},
                                              Subtitle.get_subtitle_by_id(
                                                  bangumi['subtitle_group'])))
                else:
                    subtitle_group = list(map(lambda x: {'name': x['name'], 'id': x['id']},
                                              Subtitle.get_subtitle_by_id(
                                                  bangumi['subtitle_group'].split(', ' ''))))

                r[day][index]['subtitle_group'] = subtitle_group

        if init or force_update:
            # download cover to local
            print_info('updating cover')
            bangumi_to_be_download_cover = []
            for daily_bangumi in result.values():
                for bangumi in daily_bangumi:
                    bangumi_to_be_download_cover.append(bangumi.copy())
            for bangumi in tqdm.tqdm(bangumi_to_be_download_cover):
                    self.download_cover(bangumi['cover'])

                    pass
        return r

    def download_cover(self, cover_url):
        file_path = os.path.join(bgmi.config.BGMI_PATH, 'bangumi/cover')
        file_path = os.path.join(file_path, cover_url[1:])
        dir_name = os.path.dirname(file_path)
        if not glob.glob(dir_name):
            os.makedirs(dir_name)
        if glob.glob(file_path):
            pass
        else:
            url = '{}/{}'.format(self.cover_url, cover_url)
            if os.environ.get('DEV', False):
                url = url.replace('https://', 'http://localhost:8092/https/')
            r = requests.get(url)
            with open(file_path, 'wb+') as f:
                f.write(r.content)

    def get_maximum_episode(self, bangumi, subtitle=True, ignore_old_row=True, max_page=MAX_PAGE):
        followed_filter_obj = Filter(bangumi_name=bangumi.name)
        followed_filter_obj.select_obj()

        subtitle_group = followed_filter_obj.subtitle if followed_filter_obj and subtitle else None
        include = followed_filter_obj.include if followed_filter_obj and subtitle else None
        exclude = followed_filter_obj.exclude if followed_filter_obj and subtitle else None
        regex = followed_filter_obj.regex if followed_filter_obj and subtitle else None

        data = [i for i in self.fetch_episode(_id=bangumi.keyword, name=bangumi.name,
                                              subtitle_group=subtitle_group,
                                              include=include, exclude=exclude, regex=regex, max=max_page)
                if i['episode'] is not None]

        if ignore_old_row:
            data = [row for row in data if row['time'] > int(time.time()) - 3600 * 24 * 30 * 3]  # three month

        if data:
            bangumi = max(data, key=lambda _i: _i['episode'])
            # pprint(bangumi)
            # pprint(data)
            return bangumi, data
        else:
            return {'episode': 0}, []

    def fetch_episode(self, _id, name='', **kwargs):
        result = []

        subtitle_group = kwargs.get('subtitle_group', None)
        include = kwargs.get('include', None)
        exclude = kwargs.get('exclude', None)
        regex = kwargs.get('regex', None)
        max_page = int(kwargs.get('max', int(MAX_PAGE)))

        if subtitle_group and subtitle_group.split(', '):
            condition = subtitle_group.split(', ')
            response_data = self.fetch_episode_of_bangumi(bangumi_id=_id, subtitle_list=condition)
        else:
            response_data = self.fetch_episode_of_bangumi(bangumi_id=_id, max_page=max_page)

        for info in response_data:
            if '合集' not in info['title']:
                info['name'] = name
                result.append(info)
                # result.append({
                #     'download': info['magnet'],
                #     'name': name,
                #     'subtitle_group': info['team_id'],
                #     'title': info['title'],
                #     'episode': self.parse_episode(info['title']),
                #     'time': int(time.mktime(datetime.datetime.strptime(info['publish_time'].split('.')[0],
                #                                                        "%Y-%m-%dT%H:%M:%S").timetuple()))
                # })

        if include:
            include_list = list(map(lambda s: s.strip(), include.split(',')))
            result = list(filter(lambda s: True if all(map(lambda t: t in s['title'],
                                                           include_list)) else False, result))

        if exclude:
            exclude_list = list(map(lambda s: s.strip(), exclude.split(',')))
            result = list(filter(lambda s: True if all(map(lambda t: t not in s['title'],
                                                           exclude_list)) else False, result))

        if regex:
            try:
                match = re.compile(regex)
                result = list(filter(lambda s: True if match.findall(s['title']) else False, result))
            except re.error:
                pass

        # pprint(result)
        return result

    def search_by_keyword(self, keyword, count):
        return []

    def fetch_bangumi_calendar_and_subtitle_group(self):
        return [], []

    def fetch_episode_of_bangumi(self, bangumi_id, subtitle_list=None, max_page=MAX_PAGE):
        return []


def get_response(url, method='GET', **kwargs):
    # kwargs['proxies'] = {'http': "http://localhost:1080"}
    if os.environ.get('DEV'):
        url = url.replace('https://', 'http://localhost:8092/https/')
    if os.environ.get('DEBUG'):
        print_info('Request URL: {0}'.format(url))
    try:
        if os.environ.get('DEBUG'):
            print(getattr(requests, method.lower())(url, **kwargs).text)
        return getattr(requests, method.lower(), )(url, **kwargs).json()
    except requests.ConnectionError:
        print_error('error: failed to establish a new connection')
    except ValueError:
        print_error('error: server returned data maybe not be json, please contact ricterzheng@gmail.com')
