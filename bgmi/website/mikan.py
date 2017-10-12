# coding=utf-8
from __future__ import print_function, unicode_literals

import os
import time
from multiprocessing.pool import ThreadPool

import bs4
import requests
from bs4 import BeautifulSoup

from bgmi.config import MAX_PAGE
from bgmi.website.base import BaseWebsite

week = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
server_root = 'https://mikanani.me/'


def get_weekly_bangumi():
    """
    network
    """
    r = requests.get(server_root)
    soup = BeautifulSoup(r.text, 'lxml')
    sunday = soup.find('div', attrs={'class': 'sk-bangumi', 'data-dayofweek': "0"})
    monday = soup.find('div', attrs={'class': 'sk-bangumi', 'data-dayofweek': "1"})
    tuesday = soup.find('div', attrs={'class': 'sk-bangumi', 'data-dayofweek': "2"})
    wednesday = soup.find('div', attrs={'class': 'sk-bangumi', 'data-dayofweek': "3"})
    thursday = soup.find('div', attrs={'class': 'sk-bangumi', 'data-dayofweek': "4"})
    friday = soup.find('div', attrs={'class': 'sk-bangumi', 'data-dayofweek': "5"})
    saturday = soup.find('div', attrs={'class': 'sk-bangumi', 'data-dayofweek': "6"})
    return [sunday, monday, tuesday, wednesday, thursday, friday, saturday]


def parser_day_bangumi(soup):
    """

    :param soup:
    :type soup: bs4.Tag
    :return: list
    :rtype: list[dict]
    """
    li = []
    for soup in soup.find_all('li'):
        url = soup.select_one('a')
        span = soup.find('span')
        if url:
            name = url['title']
            url = url['href']
            assert isinstance(url, str)
            bangumi_id = url.split('/')[-1]
            soup.find('li', )
            li.append({'name': name, 'keyword': bangumi_id, 'cover': span['data-src']})
    return li


def parser_subtitle_of_bangumi(bangumi_id):
    """network"""
    bangumi_id = int(bangumi_id)
    url = server_root + "Home/ExpandBangumi"
    data = {'bangumiId': bangumi_id, 'showSubscribed': False}
    r = requests.post(url, data=data, ).text
    soup = BeautifulSoup(r, 'lxml')
    g = soup.find('ul', class_='list-unstyled res-ul')
    subtitle_list = []
    for li in g.find_all('li', class_='js-expand_bangumi-subgroup', ):
        subgroup_index = li['data-bangumisubgroupindex']
        name = li.find('div', class_='sk-col tag-res-name').text
        _id = li.find('div', class_='btn-primary ladda-button sk-col tag-sub js-subscribe_bangumi')[
            'data-subtitlegroupid']
        id_div = li.find('div', class_=['js-subscribe_bangumi'])
        subgroup_div = soup.find('div', class_='js-expand_bangumi-subgroup-{}-episodes'.format(subgroup_index))
        ul_e = subgroup_div.find('ul', class_='list-unstyled res-detail-ul')
        episode_list = []
        for li2 in ul_e.find_all('li'):
            magnet_url = li2.find('a', class_='js-magnet magnet-link')
            episode_title = li2.find('a', class_='magnet-link-wrap')
            if magnet_url:
                episode_list.append({
                    '_id': _id,
                    'title': episode_title.text,
                    'url': magnet_url['data-clipboard-text'],
                    # 'url': 'mag',
                    'publish_time': li2.find('div', class_='sk-col res-date').text
                })
        subtitle_list.append({
            'id': id_div['data-subtitlegroupid'],
            'name': name,
            'episode': [] if not episode_list else episode_list
        })
    return subtitle_list


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
        r = requests.get(server_root + "Home/Search", params={'searchstr': keyword}).text
        s = BeautifulSoup(r, 'lxml')
        td_list = s.find_all('tr', attrs={'class': 'js-search-results-row'})  # type:list[bs4.Tag]
        for tr in td_list:
            title = tr.find('a', class_='magnet-link-wrap').text
            time_string = tr.find_all('td')[2].string
            result.append({
                'download': tr.find('a', class_='magnet-link').attrs.get('data-clipboard-text', ''),
                'name': keyword,
                'title': title,
                'episode': self.parse_episode(title),
                'time': int(time.mktime(time.strptime(time_string, "%Y/%m/%d %H:%M")))
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

        result = []
        if os.environ.get('DEBUG', False):
            print(server_root + 'Bangumi/{}'.format(bangumi_id))
        r = requests.get(server_root + 'Home/Bangumi/{}'.format(bangumi_id)).text

        soup = BeautifulSoup(r, 'lxml')
        # name = soup.find('p', class_='bangumi-title').text
        container = soup.find('div', class_='central-container')  # type:bs4.Tag
        episode_container_list = {}
        for index, tag in enumerate(container.contents):
            if hasattr(tag, 'attrs'):
                subtitle_id = tag.attrs.get('id', False)
                if subtitle_list:
                    if subtitle_id in subtitle_list:
                        episode_container_list[tag.attrs.get('id', None)] = tag.find_next_sibling('table')
                else:
                    if subtitle_id:
                        episode_container_list[tag.attrs.get('id', None)] = tag.find_next_sibling('table')

        for subtitle_id, container in episode_container_list.items():
            for tr in container.find_all('tr')[1:]:
                title = tr.find('a', class_='magnet-link-wrap').text
                time_string = tr.find_all('td')[2].string
                result.append({
                    'download': tr.find('a', class_='magnet-link').attrs.get('data-clipboard-text', ''),
                    'subtitle_group': str(subtitle_id),
                    'title': title,
                    'episode': self.parse_episode(title),
                    'time': int(time.mktime(time.strptime(time_string, "%Y/%m/%d %H:%M")))
                })

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
        for index, day in enumerate(get_weekly_bangumi()):
            for obj in parser_day_bangumi(day):
                obj['update_time'] = week[index]
                bangumi_result.append(obj)

        def thread(bangumi):
            subtitle_list = parser_subtitle_of_bangumi(bangumi_id=bangumi['keyword'])
            return subtitle_list

        p = ThreadPool(4)
        r = p.map(thread, bangumi_result)
        p.close()

        for index, (bangumi, subtitle_list) in enumerate(zip(bangumi_result, r)):
            bangumi_result[index]['subtitle_group'] = list(map(lambda x: x['id'], subtitle_list))
            bangumi_result[index]['name'] = bangumi['name']
            bangumi_result[index]['status'] = 0
            for subtitle in subtitle_list:
                subtitle_result.append({'id': subtitle['id'], 'name': subtitle['name']})
        return bangumi_result, subtitle_result
