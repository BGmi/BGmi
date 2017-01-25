# coding=utf-8
from __future__ import print_function, unicode_literals

import time
import datetime
import re
import string
from collections import defaultdict
from itertools import chain

import requests
from bs4 import BeautifulSoup

import bgmi.config
from bgmi.config import FETCH_URL, DETAIL_URL, MAX_PAGE
from bgmi.models import Bangumi, Followed, Filter, STATUS_FOLLOWED, STATUS_UPDATED
from bgmi.utils.utils import print_error, print_warning, print_info, unicodeize, \
    test_connection, bug_report, get_terminal_col, _, GREEN, YELLOW, COLOR_END
import bgmi.patches.bangumi
import bgmi.patches.keyword

if bgmi.config.IS_PYTHON3:
    _unicode = str
else:
    _unicode = unicode

BANGUMI_MATCH = re.compile("(?P<update_time>sun|mon|tue|wed|thu|fri|sat)"
                           "array\.push\(\['.*?','(?P<name>.*?)','(?P<ke"
                           "yword>.*?)','(?P<subtitle_group>.*?)','.*?'"
                           "\]\)")

SUBTITLE_MATCH = re.compile("<a href=\".*?\">(.*?)</a>")


def bangumi_calendar(force_update=False, today=False, followed=False, save=True):
    env_columns = get_terminal_col()

    if env_columns < 36:
        print_warning('terminal window is too small.')
        env_columns = 36

    row = int(env_columns / 36 if env_columns / 36 <= 3 else 3)

    if force_update and not test_connection():
        force_update = False
        print_warning('network is unreachable')

    if force_update:
        print_info('fetching bangumi info ...')
        Bangumi.delete_all()
        weekly_list = fetch(save=save, status=True)
    else:
        if followed:
            weekly_list_followed = Bangumi.get_all_bangumi(status=STATUS_FOLLOWED)
            weekly_list_updated = Bangumi.get_all_bangumi(status=STATUS_UPDATED)
            weekly_list = defaultdict(list)
            for k, v in chain(weekly_list_followed.items(), weekly_list_updated.items()):
                weekly_list[k].extend(v)
        else:
            weekly_list = Bangumi.get_all_bangumi()

    if not weekly_list:
        if not followed:
            print_warning('warning: no bangumi schedule, fetching ...')
            weekly_list = fetch(save=save)
        else:
            print_warning('you have not subscribed any bangumi')

    def shift(seq, n):
        n = n % len(seq)
        return seq[n:] + seq[:n]

    def print_line():
        num = 33
        # print('+', '-' * num, '+', '-' * num, '+', '-' * num, '+')
        split = '-' * num + '   '
        print(split * row)

    if today:
        weekday_order = (Bangumi.week[datetime.datetime.today().weekday()], )
    else:
        weekday_order = shift(Bangumi.week, datetime.datetime.today().weekday())

    spacial_append_chars = ['Ⅱ', 'Ⅲ', '♪', 'Δ', '×', '☆']
    spacial_remove_chars = []
    for index, weekday in enumerate(weekday_order):
        if weekly_list[weekday.lower()]:
            print('%s%s. %s' % (GREEN,
                                weekday if not today else 'Bangumi Schedule for Today (%s)' % weekday, COLOR_END),
                  end='')
            if not followed:
                print()
                print_line()

            for i, bangumi in enumerate(weekly_list[weekday.lower()]):
                if isinstance(bangumi['name'], _unicode):
                    # bangumi['name'] = bangumi['name']
                    pass

                if bangumi['status'] in (STATUS_UPDATED, STATUS_FOLLOWED) and 'episode' in bangumi:
                    bangumi['name'] = '%s(%d)' % (bangumi['name'], bangumi['episode'])

                half = len(re.findall('[%s]' % string.printable, bangumi['name']))
                full = (len(bangumi['name']) - half)
                space_count = 34 - (full * 2 + half)

                for s in spacial_append_chars:
                    if s in bangumi['name']:
                        space_count += 1

                for s in spacial_remove_chars:
                    if s in bangumi['name']:
                        space_count -= 1

                if bangumi['status'] == STATUS_FOLLOWED:
                    bangumi['name'] = '%s%s%s' % (YELLOW, bangumi['name'], COLOR_END)

                if bangumi['status'] == STATUS_UPDATED:
                    bangumi['name'] = '%s%s%s' % (GREEN, bangumi['name'], COLOR_END)

                if followed:
                    if i > 0:
                        print(' ' * 5, end='')
                    print(bangumi['name'], bangumi['subtitle_group'])
                else:
                    print(' ' + bangumi['name'], ' ' * space_count, end='')
                    if (i + 1) % row == 0 or i + 1 == len(weekly_list[weekday.lower()]):
                        print()

            if not followed:
                print()
                # print_line()


def get_response(url):
    try:
        return unicodeize(requests.get(url).content)
    except requests.ConnectionError:
        print_error('error: failed to establish a new connection')


def process_subtitle(data):
    '''get subtitle group name from links
    '''
    special_subtitle_group = ['A.I.R.nes', ]

    result = SUBTITLE_MATCH.findall(data)

    '''
    subtitle_list = []
    for i in result:
        s_list = []
        for s in special_subtitle_group:
            if s in i:
                index_of_s = i.index(s)
                s_list.append(i[index_of_s:(len(s)+index_of_s)])
                i = i[0:index_of_s] + i[(len(s)+index_of_s):]

        subtitle_list.extend(i.split('.'))
        subtitle_list.extend(s_list)
    '''
    # ['', 'a'] -> ['a']
    return [i for i in result if i]


def parser_bangumi(data, group_by_weekday=True, status=False):
    '''match weekly bangumi list from data
    '''
    result = BANGUMI_MATCH.finditer(data)
    if group_by_weekday:
        weekly_list = defaultdict(list)
    else:
        weekly_list = []
    for i in result:
        bangumi_item = i.groupdict()
        bangumi_item['status'] = 0
        bangumi_item['subtitle_group'] = process_subtitle(bangumi_item['subtitle_group'])
        if status:
            f = Followed(bangumi_name=bangumi_item['name']).select(one=True, fields='status')
            if f:
                bangumi_item['status'] = f['status']

        if group_by_weekday:
            weekly_list[bangumi_item['update_time']].append(bangumi_item)
        else:
            weekly_list.append(bangumi_item)

    if not weekly_list:
        bug_report()
    return weekly_list


def fetch(save=False, group_by_weekday=True, status=False):
    response = get_response(FETCH_URL)
    if not response:
        return

    result = parser_bangumi(response, group_by_weekday=group_by_weekday, status=status)
    if save:
        if group_by_weekday:
            data = parser_bangumi(response, group_by_weekday=False)
        else:
            data = result

        for bangumi in data:
            save_data(bangumi)

    return result


def save_data(data):
    b = Bangumi(**data)
    b.save()


FETCH_EPISODE_ZH = re.compile("[第]\s?(\d{1,2})\s?[話|话|集]")
FETCH_EPISODE_WITH_BRACKETS = re.compile('(?:【|\[)(\d+)\s?(?:END)?(?:】|\])')
FETCH_EPISODE_ONLY_NUM = re.compile('^([\d]{2,})$')
FETCH_EPISODE = (FETCH_EPISODE_ZH, FETCH_EPISODE_WITH_BRACKETS, FETCH_EPISODE_ONLY_NUM)


def parse_episode(data):
    _ = FETCH_EPISODE_ZH.findall(data)
    if _ and _[0].isdigit():
        return int(_[0])

    _ = FETCH_EPISODE_WITH_BRACKETS.findall(data)
    if _ and _[0].isdigit():
        return int(_[0])

    for split_token in ['【', '[', ' ']:
        for i in data.split(split_token):
            for regexp in FETCH_EPISODE:
                match = regexp.findall(i)
                if match and match[0].isdigit():
                    return int(match[0])
    return 0


def fetch_episode(keyword, name='', subtitle_group=None, include=None, exclude=None):
    result = []
    keyword = bgmi.patches.keyword.main(name, keyword)

    for page in range(1, int(MAX_PAGE)+1):
        response = get_response(DETAIL_URL.replace('[PAGE]', str(page)) + keyword)

        if not response:
            break

        b = BeautifulSoup(response, 'lxml')
        container = b.find('table', attrs={'class': 'tablesorter'})

        if not container:
            break

        for info in container.tbody.find_all('tr'):
            bangumi_update_info = {}
            if '動畫' not in unicodeize(info.text):
                continue

            for i, detail in enumerate(info.find_all('td')):
                if i == 0:
                    row_time = int(time.mktime(datetime.datetime.strptime(detail.span.text,
                                                                          "%Y/%m/%d %H:%M").timetuple()))
                    bangumi_update_info['time'] = row_time
                if i == 2:
                    title = detail.find('a', attrs={'target': '_blank'}).text.strip()
                    subtitle = detail.find('span', attrs={'class': 'tag'})
                    subtitle = subtitle.a.text.strip() if subtitle else ''
                    bangumi_update_info['name'] = name
                    bangumi_update_info['title'] = title
                    bangumi_update_info['subtitle_group'] = subtitle
                    bangumi_update_info['episode'] = parse_episode(title)
                if i == 3:
                    bangumi_update_info['download'] = detail.find('a').attrs.get('href')

            # filter subtitle group
            if subtitle_group:
                subtitle_group_list = map(lambda s: s.strip(), subtitle_group.split(','))
                for s in subtitle_group_list:
                    if _(s) in _(bangumi_update_info['subtitle_group']):
                        result.append(bangumi_update_info)
            else:
                result.append(bangumi_update_info)

            if include:
                include_list = map(lambda s: s.strip(), include.split(','))
                result = list(filter(lambda s: True if all(map(lambda t: _(t) in _(s['title']),
                                                               include_list)) else False, result))

            if exclude:
                exclude_list = map(lambda s: s.strip(), exclude.split(','))
                result = list(filter(lambda s: True if all(map(lambda t: _(t) not in _(s['title']),
                                                               exclude_list)) else False, result))

    result = bgmi.patches.bangumi.main(data=result)
    return result


def get_maximum_episode(bangumi, subtitle=True, ignore_old_row=True):

    followed_filter_obj = Filter(bangumi_name=bangumi.name)
    followed_filter_obj.select_obj()

    subtitle_group = followed_filter_obj.subtitle if followed_filter_obj and subtitle else None
    include = followed_filter_obj.include if followed_filter_obj and subtitle else None
    exclude = followed_filter_obj.exclude if followed_filter_obj and subtitle else None

    data = [i for i in fetch_episode(keyword=bangumi.keyword, name=bangumi.name,
                                     subtitle_group=subtitle_group,
                                     include=include, exclude=exclude)
            if i['episode'] is not None]

    if ignore_old_row:
        data = [row for row in data if row['time'] > int(time.time()) - 3600 * 24 * 30 * 3]  # three month

    if data:
        bangumi = max(data, key=lambda i: i['episode'])
        return bangumi, data
    else:
        return {'episode': 0}, []


if __name__ == '__main__':
    # fetch(save=True, group_by_weekday=False)
    b = Bangumi(name='槍彈辯駁3未來篇')
    b.select_obj()
    a, _ = get_maximum_episode(b)
    print(a['episode'])
