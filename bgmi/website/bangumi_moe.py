# coding=utf-8
from __future__ import print_function, unicode_literals

import datetime
import os
import time

import requests

from bgmi.config import (LANG, MAX_PAGE, BANGUMI_MOE_URL)
from bgmi.lib.models import Bangumi
from bgmi.utils import (print_info, bug_report, print_error, print_warning)
from bgmi.website.base import BaseWebsite

# tag of bangumi on bangumi.moe
BANGUMI_TAG = '549ef207fe682f7549f1ea90'

__split = '/' if not BANGUMI_MOE_URL.endswith('/') else ''
FETCH_URL = '{0}{1}api/bangumi/current'.format(BANGUMI_MOE_URL, __split)
TEAM_URL = '{0}{1}api/team/working'.format(BANGUMI_MOE_URL, __split)
NAME_URL = '{0}{1}api/tag/fetch'.format(BANGUMI_MOE_URL, __split)
DETAIL_URL = '{0}{1}api/torrent/search'.format(BANGUMI_MOE_URL, __split)
SEARCH_URL = '{0}{1}api/v2/torrent/search'.format(BANGUMI_MOE_URL, __split)
TORRENT_URL = '{0}{1}download/torrent/'.format(BANGUMI_MOE_URL, __split)
COVER_URL = 'https://bangumi.moe/'


def get_response(url, method='GET', **kwargs):
    # kwargs['proxies'] = {'http': "http://localhost:1080"}
    if os.environ.get('DEV'):  # pragma: no cover
        url = url.replace('https://', 'http://localhost:8092/https/')
    if os.environ.get('DEBUG'):  # pragma: no cover
        print_info('Request URL: {0}'.format(url))
    try:
        r = requests.request(method.lower(), url, **kwargs)
        if os.environ.get('DEBUG'):  # pragma: no cover
            print(r.text)
        return r.json()
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

        if item['name'] is None:
            item['name'] = bangumi_item['name']

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
        max_page = int(max_page)
        response_data = []
        ret = []
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
            ret.append({
                # 'download': bangumi['magnet'],
                'download': TORRENT_URL + bangumi['_id'] + '/download.torrent',
                'subtitle_group': bangumi['team_id'],
                'title': bangumi['title'],
                'episode': self.parse_episode(bangumi['title']),
                'time': int(time.mktime(datetime.datetime.strptime(bangumi['publish_time'].split('.')[0],
                                                                   "%Y-%m-%dT%H:%M:%S").timetuple()))
            })

            if os.environ.get('DEBUG'):
                print(ret[index]['download'])

        return ret

    def fetch_bangumi_calendar_and_subtitle_group(self):
        response = get_response(FETCH_URL)
        if not response:
            return []
        bangumi_result, subtitile_result = parser_bangumi(response)
        return bangumi_result, subtitile_result

    def search_by_keyword(self, keyword, count=None):
        if not count:
            count = 3

        rows = []
        result = []

        for i in range(count):
            data = get_response(SEARCH_URL, 'POST', json={'query': keyword, 'p': i + 1})
            if not 'torrents' in data:
                print_warning('No torrents in response data, please re-run')
                return []
            rows.extend(data['torrents'])

        for info in rows:
            if True:
                result.append({
                    'download': TORRENT_URL + info['_id'] + '/download.torrent',
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
