# coding=utf-8
from __future__ import print_function, unicode_literals

import imghdr
import os
import re
import time
from collections import defaultdict
from itertools import chain

from six import text_type

from bgmi.config import MAX_PAGE, GLOBAL_FILTER, ENABLE_GLOBAL_FILTER
from bgmi.lib.models import (Filter, Subtitle, STATUS_FOLLOWED, STATUS_UPDATED,
                             Bangumi, STATUS_UPDATING)
from bgmi.utils import (parse_episode, print_warning, print_info,
                        test_connection, download_cover, convert_cover_url_to_path)


class BaseWebsite(object):
    cover_url = ''
    parse_episode = staticmethod(parse_episode)

    @staticmethod
    def save_data(data):
        """
        save bangumi dict to database

        :type data: dict
        """
        b, obj_created = Bangumi.get_or_create(name=data['name'], defaults=data)
        if not obj_created:
            b.status = STATUS_UPDATING
            b.subtitle_group = Bangumi(**data).subtitle_group
            b.cover = data['cover']
            # if not b.cover.startswith(self.cover_url):
            #     b.cover = self.cover_url + data['cover']
            b.save()

    def fetch(self, save=False, group_by_weekday=True):
        bangumi_result, subtitle_group_result = self.fetch_bangumi_calendar_and_subtitle_group()
        Bangumi.delete_all()
        if subtitle_group_result:
            for subtitle_group in subtitle_group_result:
                (Subtitle.insert({Subtitle.id: text_type(subtitle_group['id']),
                                  Subtitle.name: text_type(subtitle_group['name'])})
                 .on_conflict_replace()).execute()
        if not bangumi_result:
            print('no result return None')
            return []

        for bangumi in bangumi_result:
            bangumi['cover'] = self.cover_url + bangumi['cover']

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
        """

        :return: list of bangumi followed
        :rtype: list[dict]
        """
        weekly_list_followed = Bangumi.get_updating_bangumi(status=STATUS_FOLLOWED)
        weekly_list_updated = Bangumi.get_updating_bangumi(status=STATUS_UPDATED)
        weekly_list = defaultdict(list)
        for k, v in chain(weekly_list_followed.items(), weekly_list_updated.items()):
            weekly_list[k].extend(v)
        for bangumi_list in weekly_list.values():
            for bangumi in bangumi_list:
                bangumi['subtitle_group'] = [{'name': x['name'],
                                              'id': x['id']} for x in
                                             Subtitle.get_subtitle_by_id(bangumi['subtitle_group'].split(', '))]
        return weekly_list

    def bangumi_calendar(self, force_update=False, save=True, cover=None):
        """

        :param force_update:
        :type force_update: bool

        :param save: set true to enable save bangumi data to database
        :type save: bool

        :param cover: list of cover url (of scripts) want to download
        :type cover: list[str]
        """
        if force_update and not test_connection():
            force_update = False
            print_warning('Network is unreachable')

        if force_update:
            print_info('Fetching bangumi info ...')
            self.fetch(save=save)
        weekly_list = Bangumi.get_updating_bangumi()

        if not weekly_list:
            print_warning('Warning: no bangumi schedule, fetching ...')
            weekly_list = self.fetch(save=save)

        if cover is not None:
            # download cover to local
            cover_to_be_download = cover
            for daily_bangumi in weekly_list.values():
                for bangumi in daily_bangumi:
                    _, file_path = convert_cover_url_to_path(bangumi['cover'])

                    if not (os.path.exists(file_path) and imghdr.what(file_path)):
                        cover_to_be_download.append(bangumi['cover'])

            if cover_to_be_download:
                print_info('Updating cover ...')
                download_cover(cover_to_be_download)

        return weekly_list

    def get_maximum_episode(self, bangumi, subtitle=True, ignore_old_row=True, max_page=MAX_PAGE):
        """

        :type max_page: str
        :param max_page:
        :type bangumi: object
        :type ignore_old_row: bool
        :param ignore_old_row:
        :type bangumi: Bangumi
        :param subtitle:
        :type subtitle: bool
        """
        followed_filter_obj, _ = Filter.get_or_create(bangumi_name=bangumi.name)

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
                                              include=include,
                                              exclude=exclude,
                                              regex=regex,
                                              max_page=int(max_page))
                if i['episode'] is not None]

        if ignore_old_row:
            data = [row for row in data if row['time'] > int(time.time()) - 3600 * 24 * 30 * 3]  # three month

        if data:
            bangumi = max(data, key=lambda _i: _i['episode'])
            return bangumi, data
        else:
            return {'episode': 0}, []

    def fetch_episode(self, _id, name='',
                      subtitle_group=None,
                      include=None,
                      exclude=None,
                      regex=None,
                      max_page=int(MAX_PAGE)):
        """
        :type _id: str
        :param _id:
        :type name: str
        :type subtitle_group: str
        :type include: str
        :type exclude: str
        :type regex: str
        :type max_page: int
        """
        result = []

        max_page = int(max_page)

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

        result = self.filter_keyword(data=result, regex=regex)
        return result

    @staticmethod
    def remove_duplicated_bangumi(result):
        """

        :type result: list[dict]
        """
        ret = []
        episodes = list({i['episode'] for i in result})
        for i in result:
            if i['episode'] in episodes:
                ret.append(i)
                del episodes[episodes.index(i['episode'])]

        return ret

    @staticmethod
    def filter_keyword(data, regex=None):
        """

        :type regex: str
        :param data: list of bangumi dict
        :type data: list[dict]
        """
        if regex:
            try:
                match = re.compile(regex)
                data = [s for s in data if match.findall(s['title'])]
            except re.error as e:
                if os.getenv('DEBUG'):  # pragma: no cover
                    import traceback
                    traceback.print_exc()
                    raise e
                return data

        if not ENABLE_GLOBAL_FILTER == '0':
            data = list(filter(lambda s: all(map(lambda t: t.strip().lower() not in s['title'].lower(),
                                                 GLOBAL_FILTER.split(','))), data))

        return data

    def search_by_keyword(self, keyword, count):  # pragma: no cover
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

    def fetch_bangumi_calendar_and_subtitle_group(self):  # pragma: no cover
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

    def fetch_episode_of_bangumi(self, bangumi_id, subtitle_list=None, max_page=MAX_PAGE):  # pragma: no cover
        """
        get all episode by bangumi id
        example
        ```
            [
                {
                    "download": "magnet:?xt=urn:btih:e43b3b6b53dd9fd6af1199e112d3c7ff15cab82c",
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
