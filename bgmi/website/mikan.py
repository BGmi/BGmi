import os
import time
from collections import defaultdict
from functools import reduce
from typing import List

import bs4
import requests

from bgmi.utils import parallel, parse_episode
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
        print(server_root + f'Bangumi/{bangumi_id}')
    r = requests.get(server_root + f'Home/Bangumi/{bangumi_id}').text

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
    nr = []
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
    name = '蜜柑计划'
    cover_url = server_root[:-1]

    def search_by_keyword(self, keyword, count=None):
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

    def fetch_episode_of_bangumi(self, bangumi_id, max_page, subtitle_list=None):
        if os.environ.get('DEBUG', False):  # pragma: no cover
            print(server_root + f'Bangumi/{bangumi_id}')
        r = requests.get(server_root + f'Home/Bangumi/{bangumi_id}').text

        soup = bs4.BeautifulSoup(r, 'html.parser')
        episode = parse_episodes_from_soup(soup)
        result = sum([x['episode'] for x in episode.values()], [])
        return result

    def fetch_bangumi_calendar_and_subtitle_group(self):
        bangumi_result = []
        subtitle_result = []
        bangumi_list = []
        for index, day in enumerate(get_weekly_bangumi()):
            if not day:
                print(index)
            for obj in parser_day_bangumi(day):
                bangumi_list.append(obj)

        r = parallel(parse_bangumi_details_page, [x['keyword'] for x in bangumi_list])

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
