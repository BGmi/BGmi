# coding=utf-8
from __future__ import print_function, unicode_literals

import datetime
import os
import time

import requests

from bgmi.config import (LANG, MAX_PAGE, COVER_URL, BANGUMI_MOE_URL)
from bgmi.models import Bangumi
from bgmi.utils import (print_info, bug_report, print_error)
from bgmi.website.base import BaseWebsite

# tag of bangumi on bangumi.moe
BANGUMI_TAG = '549ef207fe682f7549f1ea90'

__split = '/' if not BANGUMI_MOE_URL.endswith('/') else ''
FETCH_URL = '{0}{1}api/bangumi/current'.format(BANGUMI_MOE_URL, __split)
TEAM_URL = '{0}{1}api/team/working'.format(BANGUMI_MOE_URL, __split)
NAME_URL = '{0}{1}api/tag/fetch'.format(BANGUMI_MOE_URL, __split)
DETAIL_URL = '{0}{1}api/torrent/search'.format(BANGUMI_MOE_URL, __split)
SEARCH_URL = '{0}{1}api/v2/torrent/search'.format(BANGUMI_MOE_URL, __split)


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


def process_name(data):
    lang = 'zh_cn' if LANG not in ('zh_cn', 'zh_tw', 'ja', 'en') else LANG
    return {i['_id']: i['locale'][lang] for i in data}


def process_subtitle(data):
    """get subtitle group name from links
    """
    result = {}
    for s in data:
        # pprint(data)
        # f = Subtitle(id=s['tag_id'], name=s['name'])
        # if not f.select():
        #     f.save()
        result[s['tag_id']] = s['name']
    return result


def parser_bangumi(data):
    """match weekly bangumi list from data
    """

    ids = list(map(lambda b: b['tag_id'], data))
    subtitle = get_response(TEAM_URL, 'POST', json={'tag_ids': ids})
    name = process_name(get_response(NAME_URL, 'POST', json={'_ids': ids}))

    weekly_list = []
    subtitle_group_list = []
    for bangumi_item in data:
        subtitle_of_bangumi = process_subtitle(subtitle.get(bangumi_item['tag_id'], []))
        item = {'status': 0,
                'subtitle_group': list(subtitle_of_bangumi.keys()),
                'name': name[bangumi_item['tag_id']],
                'keyword': bangumi_item['tag_id'],
                'update_time': Bangumi.week[bangumi_item['showOn'] - 1],
                'cover': bangumi_item['cover']}
        for key, value in subtitle_of_bangumi.items():
            subtitle_group_list.append({
                'id': key,
                'name': value
            })

        weekly_list.append(item)

    if not weekly_list:
        bug_report()
    return weekly_list, subtitle_group_list


class BangumiMoe(BaseWebsite):
    cover_url = COVER_URL

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

        response_data = []
        if subtitle_list:
            for subtitle_id in subtitle_list:
                data = {'tag_id': [bangumi_id, subtitle_id, BANGUMI_TAG]}
                response = get_response(DETAIL_URL, 'POST', json=data)
                response_data.extend(response['torrents'])
        else:
            for i in range(max_page):
                if max_page > 1:
                    print_info('Fetch page {0} ...'.format(i + 1))
                data = {'tag_id': [bangumi_id, BANGUMI_TAG], 'p': i + 1}
                response = get_response(DETAIL_URL, 'POST', json=data)
                if response:
                    response_data.extend(response['torrents'])
        for index, bangumi in enumerate(response_data):
            response_data[index] = {
                'download': bangumi['magnet'],
                'subtitle_group': bangumi['team_id'],
                'title': bangumi['title'],
                'episode': self.parse_episode(bangumi['title']),
                'time': int(time.mktime(datetime.datetime.strptime(bangumi['publish_time'].split('.')[0],
                                                                   "%Y-%m-%dT%H:%M:%S").timetuple()))
            }

        return response_data

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
        response = get_response(FETCH_URL)
        if not response:
            return []

        bangumi_result, subtitile_result = parser_bangumi(response)

        return bangumi_result, subtitile_result

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

        rows = []
        result = []

        for i in range(count):
            data = get_response(SEARCH_URL, 'POST', json={'query': keyword, 'p': i + 1})
            rows.extend(data['torrents'])

        for info in rows:
            if True:
                result.append({
                    'download': info['magnet'],
                    'name': keyword,
                    'subtitle_group': info['team_id'],
                    'title': info['title'],
                    'episode': self.parse_episode(info['title']),
                    'time': int(time.mktime(datetime.datetime.strptime(info['publish_time'].split('.')[0],
                                                                       "%Y-%m-%dT%H:%M:%S").timetuple()))
                })

        # Avoid bangumi collection. It's ok but it will waste your traffic and bandwidth.
        result = result[::-1]
        return result
