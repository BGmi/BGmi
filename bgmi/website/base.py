# coding=utf-8
from __future__ import print_function, unicode_literals

import glob
import os
import re
import time
from collections import defaultdict
from itertools import chain
from multiprocessing.pool import ThreadPool

import requests

from bgmi.config import MAX_PAGE, SAVE_PATH, IS_PYTHON3
from bgmi.models import Bangumi, Filter, Subtitle, STATUS_FOLLOWED, STATUS_UPDATED
from bgmi.script import ScriptRunner
from bgmi.utils import (parse_episode, print_warning, print_info,
                        test_connection, normalize_path)

if IS_PYTHON3:
    _unicode = str
else:
    _unicode = unicode


class BaseWebsite(object):
    cover_url = ''
    parse_episode = staticmethod(parse_episode)

    @staticmethod
    def save_data(data):
        b = Bangumi(**data)
        b.save()

    def fetch(self, save=False, group_by_weekday=True):
        bangumi_result, subtitle_group_result = self.fetch_bangumi_calendar_and_subtitle_group()
        if subtitle_group_result:
            for subtitle_group in subtitle_group_result:
                s, if_created = Subtitle.get_or_create(id=_unicode(subtitle_group['id']),
                                                       name=_unicode(subtitle_group['name']))
                if if_created:
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

    @staticmethod
    def followed_bangumi():
        weekly_list_followed = Bangumi.get_all_bangumi(status=STATUS_FOLLOWED)
        weekly_list_updated = Bangumi.get_all_bangumi(status=STATUS_UPDATED)
        weekly_list = defaultdict(list)
        for k, v in chain(weekly_list_followed.items(), weekly_list_updated.items()):
            weekly_list[k].extend(v)
        for bangumi_list in weekly_list.values():
            for bangumi in bangumi_list:
                bangumi['subtitle_group'] = [{'name': x['name'], 'id': x['id']}
                                             for x in Subtitle.get_subtitle(bangumi['subtitle_group'].split(', '))]
        return weekly_list

    def bangumi_calendar(self, force_update=False, save=True, cover=False):
        if force_update and not test_connection():
            force_update = False
            print_warning('network is unreachable')

        if force_update:
            print_info('fetching bangumi info ...')
            Bangumi.delete_all()
            weekly_list = self.fetch(save=save)
        else:
            weekly_list = Bangumi.get_all_bangumi()
        if not weekly_list:
            print_warning('warning: no bangumi schedule, fetching ...')
            weekly_list = self.fetch(save=save)
        for key, value in weekly_list.items():
            for bangumi in value:
                bangumi['cover'] = self.cover_url + bangumi['cover']
        runner = ScriptRunner()
        patch_list = runner.get_models_dict()
        for i in patch_list:
            weekly_list[i['update_time'].lower()].append(i)

        if cover:
            # download cover to local
            cover_to_be_download = []
            for daily_bangumi in weekly_list.values():
                for bangumi in daily_bangumi:
                    _, file_path = self.convert_cover_to_path(bangumi['cover'])

                    if not glob.glob(file_path):
                        cover_to_be_download.append(bangumi['cover'])

            if cover_to_be_download:
                print_info('updating cover')
                self.download_cover(cover_to_be_download)

        return weekly_list

    def download_cover(self, cover_url_list):
        """

        :param cover_url_list:
        :type cover_url_list: list
        :return:
        """

        p = ThreadPool(4)
        content_list = p.map(requests.get, cover_url_list)
        for index, r in enumerate(content_list):
            dir_path, file_path = self.convert_cover_to_path(cover_url_list[index])
            if not glob.glob(dir_path):
                os.makedirs(dir_path)
            with open(file_path, 'wb') as f:
                f.write(r.content)
        p.close()

    @staticmethod
    def convert_cover_to_path(cover_url):
        """
        convert bangumi cover to file path

        :param cover_url: bangumi cover path
        :type cover_url:str
        :rtype: str,str
        :return:file_path, dir_path
        """

        cover_url = normalize_path(cover_url)
        file_path = os.path.join(SAVE_PATH, 'cover')
        file_path = os.path.join(file_path, cover_url)
        dir_path = os.path.dirname(file_path)

        return dir_path, file_path

    def get_maximum_episode(self, bangumi, subtitle=True, ignore_old_row=True, max_page=MAX_PAGE):

        followed_filter_obj = Filter.get(bangumi_name=bangumi.name)

        if followed_filter_obj and subtitle:
            subtitle_group = followed_filter_obj.subtitle
        else:
            subtitle_group = None

        if followed_filter_obj and subtitle:
            include = followed_filter_obj.include
        else:
            include = None

        if followed_filter_obj and subtitle:
            exclude = followed_filter_obj.exclude
        else:
            exclude = None

        if followed_filter_obj and subtitle:
            regex = followed_filter_obj.regex
        else:
            regex = None

        data = [i for i in self.fetch_episode(_id=bangumi.keyword, name=bangumi.name,
                                              subtitle_group=subtitle_group,
                                              include=include, exclude=exclude, regex=regex, max=max_page)
                if i['episode'] is not None]

        if ignore_old_row:
            data = [row for row in data if row['time'] > int(time.time()) - 3600 * 24 * 30 * 3]  # three month

        if data:
            bangumi = max(data, key=lambda _i: _i['episode'])
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

        return result

    @staticmethod
    def remove_duplicated_bangumi(result):
        ret = []
        episodes = list({i['episode'] for i in result})
        for i in result:
            if i['episode'] in episodes:
                ret.append(i)
                del episodes[episodes.index(i['episode'])]

        return ret

    def search_by_keyword(self, keyword, count):
        """
        return a list of dict with at least 4 key: download, name, title, episode
        example:
        ```
            [
                {
                    'name':"路人女主的养成方法",
                    'download': 'magnet:?xt=urn:btih:what ever',
                    'title': "[澄空学园] 路人女主的养成方法 第12话 MP4 720p  完",
                    'episode': 12
                },
            ]

        :param keyword: search key word
        :type keyword: str
        :param count: how many page to fetch from website
        :type count: int

        :return: list of episode search result
        :rtype: list[dict]
        """
        raise NotImplementedError

    def fetch_bangumi_calendar_and_subtitle_group(self):
        """
        return a list of all bangumi and a list of all subtitle group

        list of bangumi dict:
        update time should be one of ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        example:
        ```
            [
                {
                    "status": 0,
                    "subtitle_group": [
                        "123",
                        "456"
                    ],
                    "name": "名侦探柯南",
                    "keyword": "1234", #bangumi id
                    "update_time": "Sat",
                    "cover": "data/images/cover1.jpg"
                },
            ]
        ```

        list of subtitle group dict:
        example:
        ```
            [
                {
                    'id': '233',
                    'name': 'bgmi字幕组'
                }
            ]
        ```


        :return: list of bangumi, list of subtitile group
        :rtype: (list[dict], list[dict])
        """
        raise NotImplementedError

    def fetch_episode_of_bangumi(self, bangumi_id, subtitle_list=None, max_page=MAX_PAGE):
        """
        get all episode by bangumi id
        example
        ```
            [
                {
                    "download": "magnet:?xt=urn:btih:e43b3b6b53dd9fd6af1199e112d3c7ff15cab82c",
                    "name": "来自深渊",
                    "subtitle_group": "58a9c1c9f5dc363606ab42ec",
                    "title": "【喵萌奶茶屋】★七月新番★[来自深渊/Made in Abyss][07][GB][720P]",
                    "episode": 0,
                    "time": 1503301292
                },
            ]
        ```

        :param bangumi_id: bangumi_id
        :param subtitle_list: list of subtitle group
        :type subtitle_list: list
        :param max_page: how many page you want to crawl if there is no subtitle list
        :type max_page: int
        :return: list of bangumi
        :rtype: list[dict]
        """
        raise NotImplementedError
