import os
import re
import time as Time
import urllib.parse

import requests
from bs4 import BeautifulSoup

from bgmi.website.base import BaseWebsite

unquote = urllib.parse.unquote
SHARE_DMHY_URL = 'https://share.dmhy.org'

base_url = SHARE_DMHY_URL

cover_url = SHARE_DMHY_URL


def parse_bangumi_with_week_days(content, update_time, array_name):
    r = re.compile(array_name + r'\.push\(\[\'(.*?)\',\'(.*?)\',\'(.*?)\',\'(.*?)\',\'(.*?)\'\]\)')
    ret = r.findall(content)

    bangumi_list = []
    subtitle_list = []

    for bangumi_row in ret:
        bangumi = {
            'status': 0,
            'subtitle_group': [],
            'name': '',
            'keyword': '',  # bangumi id
            'update_time': '',
            'cover': ''
        }
        (cover_url, name, keyword, subtitle_raw, _) = bangumi_row
        cover = re.findall('(/images/.*)$', cover_url)[0]

        bs = BeautifulSoup(subtitle_raw, 'html.parser')
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
                'name': subtitle_group_name,
            })

            bangumi['subtitle_group'].append(subtitle_group_id)

        bangumi['name'] = name
        bangumi['update_time'] = update_time
        bangumi['keyword'] = keyword
        bangumi['cover'] = cover_url + cover

        # append to bangumi_list
        bangumi_list.append(bangumi)

    return bangumi_list, subtitle_list


def parse_subtitle_list(content):
    subtitle_list = []

    bs = BeautifulSoup(content, 'html.parser')
    li_list = bs.find_all('li', {'class': 'team-item'})

    for li in li_list:
        subtitle_group_name = li.span.a.get('title')
        subtitle_group_id_raw = re.findall('team_id/(.+)$', li.span.a.get('href'))

        if (len(subtitle_group_id_raw) == 0) or subtitle_group_name == '':
            continue

        subtitle_group_id = subtitle_group_id_raw[0]
        # append to subtitle_list
        subtitle_list.append({'id': subtitle_group_id, 'name': subtitle_group_name})

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
    name = '动漫花园'
    data_source_id = 'dmhy'

    def search_by_keyword(self, keyword, count=None):
        if count is None:
            count = 3

        result = []
        search_url = base_url + '/topics/list/'
        for i in range(count):

            params = {'keyword': keyword, 'page': i + 1}

            if os.environ.get('DEBUG', False):  # pragma: no cover
                print(search_url, params)

            r = requests.get(search_url, params=params).text
            bs = BeautifulSoup(r, 'html.parser')

            table = bs.find('table', {'id': 'topic_list'})
            if table is None:
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
                time = int(Time.mktime(Time.strptime(time_string, '%Y/%m/%d %H:%M')))

                result.append({
                    'name': name,
                    'title': title,
                    'download': download,
                    'episode': episode,
                    'time': time,
                })

        return result

    def fetch_bangumi_calendar_and_subtitle_group(self):
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

        r = requests.get(url).text

        for update_time, array_name in week_days_mapping:
            (b_list, s_list) = parse_bangumi_with_week_days(r, update_time, array_name)
            bangumi_list.extend(b_list)
            subtitle_list.extend(s_list)

        # fetch subtitle
        url = base_url + '/team/navigate/'

        r = requests.get(url).text

        subtitle_list.extend(parse_subtitle_list(r))

        # unique
        subtitle_list = unique_subtitle_list(subtitle_list)

        if os.environ.get('DEBUG', False):  # pragma: no cover
            print(subtitle_list)

        return (bangumi_list, subtitle_list)

    def fetch_episode_of_bangumi(self, bangumi_id, max_page, subtitle_list=None):
        result = []
        keyword = bangumi_id
        search_url = base_url + '/topics/list/'
        for i in range(max_page):

            # params = {'keyword': keyword, 'page': i + 1}

            url = search_url + '?keyword=' + keyword + '&page=' + str(i + 1)

            if os.environ.get('DEBUG', False):  # pragma: no cover
                print(url)

            r = requests.get(url).text
            bs = BeautifulSoup(r, 'html.parser')

            table = bs.find('table', {'id': 'topic_list'})
            if table is None:
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
                time = int(Time.mktime(Time.strptime(time_string, '%Y/%m/%d %H:%M')))
                subtitle_group = ''

                tag_list = td_list[2].find_all('span', {'class': 'tag'})

                for tag in tag_list:

                    href = tag.a.get('href')
                    if href is None:
                        continue

                    team_id_raw = re.findall('team_id/(.*)$', href)
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
