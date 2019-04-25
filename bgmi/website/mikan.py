import os
import time
from collections import defaultdict
from functools import reduce
from multiprocessing.pool import ThreadPool
from typing import List

import bs4
import requests

from bgmi.config import MAX_PAGE
from bgmi.utils import parse_episode
from bgmi.website.base import BaseWebsite

week = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
server_root = 'https://mikanani.me/'

Cn_week_map = {
    '星期日': 'Sun',
    '星期一': 'Mon',
    '星期二': 'Tue',
    '星期三': 'Wed',
    '星期四': 'Thu',
    '星期五': 'Fri',
    '星期六': 'Sat',
}


def get_weekly_bangumi():
    """
    network
    """
    r = requests.get(server_root)
    soup = bs4.BeautifulSoup(r.text, 'html.parser')
    for day_of_week in [x for x in range(0, 9) if x != 7]:
        d = soup.find('div', attrs={'class': 'sk-bangumi', 'data-dayofweek': str(day_of_week)})
        if d:
            yield d


def parser_day_bangumi(soup):
    """

    :param soup:
    :type soup: bs4.Tag
    :return: list
    :rtype: list[dict]
    """
    container = []
    for tag in soup.find_all('li'):
        url = tag.select_one('a')
        span = tag.find('span')
        if url:
            name = url['title']
            url = url['href']
            bangumi_id = url.split('/')[-1]
            container.append({'name': name, 'keyword': bangumi_id, 'cover': span['data-src']})
    return container


def parse_episodes_from_soup(soup: bs4.BeautifulSoup):
    container = soup.find('div', class_='central-container')  # type:bs4.Tag
    subtitle_groups = defaultdict(lambda: defaultdict(list))
    episode_container_list = {}
    for tag in container.contents:
        if hasattr(tag, 'attrs'):
            subtitle_id = tag.attrs.get('id', False)
            if subtitle_id:
                episode_container_list[tag.attrs.get('id', None)] = tag.find_next_sibling('table')

    for subtitle_id, container in episode_container_list.items():
        for tr in container.find_all('tr')[1:]:
            title = tr.find('a', class_='magnet-link-wrap').text
            time_string = tr.find_all('td')[2].string
            subtitle_groups[str(subtitle_id)]['episode'].append({
                'download': tr.find('a', class_='magnet-link').attrs.get('data-clipboard-text', ''),
                'subtitle_group': str(subtitle_id),
                'title': title,
                'episode': parse_episode(title),
                'time': int(time.mktime(time.strptime(time_string, '%Y/%m/%d %H:%M'))),
            })
    return subtitle_groups


def parse_bangumi_details_page(bangumi_id):
    if os.environ.get('DEBUG', False):  # pragma: no cover
        print(server_root + 'Bangumi/{}'.format(bangumi_id))
    r = requests.get(server_root + 'Home/Bangumi/{}'.format(bangumi_id)).text

    soup = bs4.BeautifulSoup(r, 'html.parser')

    # info
    bangumi_info = {'status': 0}
    left_container = soup.find('div', class_='pull-left leftbar-container')  # type:bs4.Tag
    title = left_container.find('p', class_='bangumi-title')
    day = title.find_next_sibling('p', class_='bangumi-info')
    bangumi_info['update_time'] = Cn_week_map[day.text[-3:]]

    subtitle_groups = parse_episodes_from_soup(soup)

    ######
    bangumi_info['subtitle_group'] = list(subtitle_groups.keys())
    nr = list()
    dv = soup.find('div', class_='leftbar-nav')
    li_list = dv.ul.find_all('li')
    for li in li_list:
        a = li.find('a')
        nr.append({
            'id': a.attrs['data-anchor'][1:],
            'name': a.text,
        })

    bangumi_info['subtitle_groups'] = nr
    return bangumi_info


class Mikanani(BaseWebsite):
    cover_url = server_root[:-1]

    def search_by_keyword(self, keyword, count=None):
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
        ```
        :param keyword: search key word
        :type keyword: str
        :param count: how many page to fetch from website
        :type count: int

        :return: list of episode search result
        :rtype: list[dict]
        """

        result = []
        r = requests.get(server_root + 'Home/Search', params={'searchstr': keyword}).text
        s = bs4.BeautifulSoup(r, 'html.parser')
        td_list = s.find_all('tr', attrs={'class': 'js-search-results-row'})  # type:List[bs4.Tag]
        for tr in td_list:
            title = tr.find('a', class_='magnet-link-wrap').text
            time_string = tr.find_all('td')[2].string
            result.append({
                'download': tr.find('a', class_='magnet-link').attrs.get('data-clipboard-text', ''),
                'name': keyword,
                'title': title,
                'episode': self.parse_episode(title),
                'time': int(time.mktime(time.strptime(time_string, '%Y/%m/%d %H:%M'))),
            })
            # print(result)
        return result

    def fetch_episode_of_bangumi(self, bangumi_id, subtitle_list=None, max_page=MAX_PAGE):
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
        if os.environ.get('DEBUG', False):  # pragma: no cover
            print(server_root + 'Bangumi/{}'.format(bangumi_id))
        r = requests.get(server_root + 'Home/Bangumi/{}'.format(bangumi_id)).text

        soup = bs4.BeautifulSoup(r, 'html.parser')
        episode = parse_episodes_from_soup(soup)
        result = sum([x['episode'] for x in episode.values()], [])
        return result

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
        bangumi_result = []
        subtitle_result = []
        bangumi_list = list()
        for index, day in enumerate(get_weekly_bangumi()):
            if not day:
                print(index)
            for obj in parser_day_bangumi(day):
                bangumi_list.append(obj)

        p = ThreadPool(4)
        r = p.map(parse_bangumi_details_page, [x['keyword'] for x in bangumi_list])
        p.close()

        for i, bangumi in enumerate(bangumi_list):
            bangumi.update(r[i])
            bangumi_result.append(bangumi)

        for x in bangumi_result:
            subtitle_result.extend(x['subtitle_groups'])

        def f(x, y):
            return x if y in x else x + [y]

        subtitle_result = reduce(f, [[]] + subtitle_result)
        subtitle_result.sort(key=lambda x: int(x['id']))

        return bangumi_result, subtitle_result
