# coding=utf-8
from __future__ import print_function, unicode_literals

import os
import re
import time as Time
import urllib

import requests
from bs4 import BeautifulSoup

from bgmi.config import (MAX_PAGE, SHARE_DMHY_URL, IS_PYTHON3)
from bgmi.utils import print_error
from bgmi.website.base import BaseWebsite

if IS_PYTHON3:
    unquote = urllib.parse.unquote
else:
    unquote = urllib.unquote

base_url = SHARE_DMHY_URL


def fetch_url(url, **kwargs):
    ret = None
    try:
        ret = requests.get(url, **kwargs).text
    except requests.ConnectionError:
        print_error('Create connection to {site}... failed'.format(site=SHARE_DMHY_URL), exit_=False)
        print_error(
            'Check internet connection or try to set a DMHY mirror site via: bgmi config SHARE_DMHY_URL <site url>')

    return ret


def parse_bangumi_with_week_days(content, update_time, array_name):
    r = re.compile(array_name + '\.push\(\[\'(.*?)\',\'(.*?)\',\'(.*?)\',\'(.*?)\',\'(.*?)\'\]\)')
    ret = r.findall(content)

    bangumi_list = []
    subtitle_list = []

    for bangumi_row in ret:
        bangumi = {
            "status": 0,
            "subtitle_group": [],
            "name": "",
            "keyword": "",  # bangumi id
            "update_time": "",
            "cover": ""
        }
        (cover_url, name, keyword, subtitle_raw, _) = bangumi_row
        cover = re.findall('(/images/.*)$', cover_url)[0]

        bs = BeautifulSoup(subtitle_raw, 'lxml')
        a_list = bs.find_all('a')

        for a in a_list:
            subtitle_group_name = a.get_text(strip=True)
            subtitle_group_id_raw = re.findall('team_id%3A(.+)$', a['href'])

            if (len(subtitle_group_id_raw) == 0) or subtitle_group_name == '':
                continue

            subtitle_group_id = subtitle_group_id_raw[0]
            # append to subtitle_list
            subtitle_list.append({
                'id': subtitle_group_id,
                'name': subtitle_group_name
            })

            bangumi['subtitle_group'].append(subtitle_group_id)
            pass

        bangumi['name'] = name
        bangumi['update_time'] = update_time
        bangumi['keyword'] = keyword
        bangumi['cover'] = cover

        # append to bangumi_list
        bangumi_list.append(bangumi)

    return bangumi_list, subtitle_list


def parse_subtitle_list(content):
    subtitle_list = []

    bs = BeautifulSoup(content, 'lxml')
    li_list = bs.find_all('li', {'class': 'team-item'})

    for li in li_list:
        subtitle_group_name = li.span.a.get('title')
        subtitle_group_id_raw = re.findall('team_id\/(.+)$', li.span.a.get('href'))

        if (len(subtitle_group_id_raw) == 0) or subtitle_group_name == '':
            continue

        subtitle_group_id = subtitle_group_id_raw[0]
        # append to subtitle_list
        subtitle_list.append({
            'id': subtitle_group_id,
            'name': subtitle_group_name
        })

    return subtitle_list


def unique_subtitle_list(raw_list):
    ret = []
    id_list = list({i['id'] for i in raw_list})
    for row in raw_list:
        if row['id'] in id_list:
            ret.append(row)
            del id_list[id_list.index(row['id'])]

    return ret


class DmhySource(BaseWebsite):
    cover_url = SHARE_DMHY_URL

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
        if count == None:
            count = 3

        result = []
        search_url = base_url + '/topics/list/'
        for i in range(count):

            params = {'keyword': keyword, 'page': i + 1}

            if os.environ.get('DEBUG', False):  # pragma: no cover
                print(search_url, params)

            r = fetch_url(search_url, params=params)
            bs = BeautifulSoup(r, 'lxml')

            table = bs.find('table', {'id': 'topic_list'})
            if table == None:
                break
            tr_list = table.tbody.find_all('tr', {'class': ''})
            for tr in tr_list:

                td_list = tr.find_all('td')

                if td_list[1].a['class'][0] != 'sort-2':
                    continue

                time_string = td_list[0].span.string
                name = keyword
                title = td_list[2].find('a', {'target': '_blank'}).get_text(strip=True)
                download = td_list[3].a['href']
                episode = self.parse_episode(title)
                time = int(Time.mktime(Time.strptime(time_string, "%Y/%m/%d %H:%M")))

                result.append({
                    'name': name,
                    'title': title,
                    'download': download,
                    'episode': episode,
                    'time': time,
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
        week_days_mapping = [
            ('Sun', 'sunarray'),
            ('Mon', 'monarray'),
            ('Tue', 'tuearray'),
            ('Wed', 'wedarray'),
            ('Thu', 'thuarray'),
            ('Fri', 'friarray'),
            ('Sat', 'satarray'),
        ]

        bangumi_list = []
        subtitle_list = []

        url = base_url + '/cms/page/name/programme.html'

        r = fetch_url(url)

        for update_time, array_name in week_days_mapping:
            (b_list, s_list) = parse_bangumi_with_week_days(r, update_time, array_name)
            bangumi_list.extend(b_list)
            subtitle_list.extend(s_list)
            pass

        # fetch subtitle
        url = base_url + '/team/navigate/'

        r = fetch_url(url)

        subtitle_list.extend(parse_subtitle_list(r))

        # unique
        subtitle_list = unique_subtitle_list(subtitle_list)

        if os.environ.get('DEBUG', False):  # pragma: no cover
            print(subtitle_list)

        return (bangumi_list, subtitle_list)

    def fetch_episode_of_bangumi(self, bangumi_id, subtitle_list=None, max_page=int(MAX_PAGE)):
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
        result = []
        keyword = bangumi_id
        search_url = base_url + '/topics/list/'
        for i in range(max_page):

            # params = {'keyword': keyword, 'page': i + 1}

            url = search_url + '?keyword=' + keyword + '&page=' + str(i + 1)

            if os.environ.get('DEBUG', False):  # pragma: no cover
                print(url)

            r = fetch_url(url)
            bs = BeautifulSoup(r, 'lxml')

            table = bs.find('table', {'id': 'topic_list'})
            if table == None:
                break
            tr_list = table.tbody.find_all('tr', {'class': ''})
            for tr in tr_list:

                td_list = tr.find_all('td')

                if td_list[1].a['class'][0] != 'sort-2':
                    continue

                time_string = td_list[0].span.string
                name = keyword
                title = td_list[2].find('a', {'target': '_blank'}).get_text(strip=True)
                download = td_list[3].a['href']
                episode = self.parse_episode(title)
                time = int(Time.mktime(Time.strptime(time_string, "%Y/%m/%d %H:%M")))
                subtitle_group = ''

                tag_list = td_list[2].find_all('span', {'class': 'tag'})

                for tag in tag_list:

                    href = tag.a.get('href')
                    if href == None:
                        continue

                    team_id_raw = re.findall('team_id\/(.*)$', href)
                    if len(team_id_raw) == 0:
                        continue
                    subtitle_group = team_id_raw[0]

                if subtitle_list:
                    if subtitle_group not in subtitle_list:
                        continue

                if os.environ.get('DEBUG', False):  # pragma: no cover
                    print(name, title, subtitle_group, download, episode, time)

                result.append({
                    'name': name,
                    'title': title,
                    'subtitle_group': subtitle_group,
                    'download': download,
                    'episode': episode,
                    'time': time,
                })

        return result

    pass
