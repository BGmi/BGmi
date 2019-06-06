import datetime
import os
import time

import requests

from bgmi.config import BANGUMI_MOE_URL, LANG
from bgmi.lib.models import Bangumi
from bgmi.website.base import BaseWebsite

# tag of bangumi on bangumi.moe
BANGUMI_TAG = '549ef207fe682f7549f1ea90'

__split = '/' if not BANGUMI_MOE_URL.endswith('/') else ''
FETCH_URL = f'{BANGUMI_MOE_URL}{__split}api/bangumi/current'
TEAM_URL = f'{BANGUMI_MOE_URL}{__split}api/team/working'
NAME_URL = f'{BANGUMI_MOE_URL}{__split}api/tag/fetch'
DETAIL_URL = f'{BANGUMI_MOE_URL}{__split}api/torrent/search'
SEARCH_URL = f'{BANGUMI_MOE_URL}{__split}api/v2/torrent/search'
TORRENT_URL = f'{BANGUMI_MOE_URL}{__split}download/torrent/'
COVER_URL = 'https://bangumi.moe/'


def process_name(data):
    lang = 'zh_cn' if LANG not in ('zh_cn', 'zh_tw', 'ja', 'en') else LANG
    return {i['_id']: i['locale'][lang] for i in data}


def process_subtitle(data):
    """get subtitle group name from links
    """
    result = {}
    for s in data:
        result[s['tag_id']] = s['name']
    return result


def parser_bangumi(data):
    """match weekly bangumi list from data
    """

    ids = list(map(lambda b: b['tag_id'], data))
    subtitle = requests.post(TEAM_URL, json={'tag_ids': ids}).json()
    name = process_name(requests.post(NAME_URL, json={'_ids': ids}).json())

    weekly_list = []
    subtitle_group_list = []
    for bangumi_item in data:
        subtitle_of_bangumi = process_subtitle(subtitle.get(bangumi_item['tag_id'], []))
        item = {
            'status': 0,
            'subtitle_group': list(subtitle_of_bangumi.keys()),
            'name': name[bangumi_item['tag_id']] or bangumi_item['name'],
            'keyword': bangumi_item['tag_id'],
            'update_time': Bangumi.week[bangumi_item['showOn'] - 1],
            'cover': bangumi_item['cover'],
        }
        for key, value in subtitle_of_bangumi.items():
            subtitle_group_list.append({'id': key, 'name': value})

        weekly_list.append(item)

    return weekly_list, subtitle_group_list


class BangumiMoe(BaseWebsite):
    cover_url = COVER_URL

    def fetch_episode_of_bangumi(self, bangumi_id, max_page, subtitle_list=None):
        max_page = int(max_page)
        response_data = []
        ret = []
        if subtitle_list:
            for subtitle_id in subtitle_list:
                data = {'tag_id': [bangumi_id, subtitle_id, BANGUMI_TAG]}
                response = requests.post(DETAIL_URL, json=data).json()
                response_data.extend(response['torrents'])
        else:
            for i in range(max_page):
                # if max_page > 1:
                #     print_info('Fetch page {0} ...'.format(i + 1))
                data = {'tag_id': [bangumi_id, BANGUMI_TAG], 'p': i + 1}
                response = requests.post(DETAIL_URL, json=data).json()
                if response:
                    response_data.extend(response['torrents'])

        for index, bangumi in enumerate(response_data):
            ret.append({
                # 'download': bangumi['magnet'],
                'download': TORRENT_URL + bangumi['_id'] + '/download.torrent',
                'subtitle_group': bangumi['team_id'],
                'title': bangumi['title'],
                'episode': self.parse_episode(bangumi['title']),
                'time': int(
                    time.mktime(
                        datetime.datetime.strptime(
                            bangumi['publish_time'].split('.')[0], '%Y-%m-%dT%H:%M:%S'
                        ).timetuple()
                    )
                )
            })

            if os.environ.get('DEBUG'):
                print(ret[index]['download'])

        return ret

    def fetch_bangumi_calendar_and_subtitle_group(self):
        response = requests.get(FETCH_URL).json()
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
            data = requests.post(SEARCH_URL, json={'query': keyword, 'p': i + 1}).json()
            if 'torrents' not in data:
                return []
            rows.extend(data['torrents'])

        for info in rows:
            result.append({
                'download': TORRENT_URL + info['_id'] + '/download.torrent',
                'name': keyword,
                'subtitle_group': info['team_id'],
                'title': info['title'],
                'episode': self.parse_episode(info['title']),
            })

        # Avoid bangumi collection. It's ok but it will waste your traffic and bandwidth.
        result = result[::-1]
        return result
