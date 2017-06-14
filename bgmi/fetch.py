# coding=utf-8
from __future__ import print_function, unicode_literals

import os
import time
import datetime
import re
import string
from collections import defaultdict
from itertools import chain

import requests

import bgmi.config
from bgmi.config import FETCH_URL, TEAM_URL, NAME_URL, DETAIL_URL, LANG, MAX_PAGE
from bgmi.models import Bangumi, Filter, Subtitle, STATUS_FOLLOWED, STATUS_UPDATED
from bgmi.utils.utils import print_error, print_warning, print_info, \
    test_connection, bug_report, get_terminal_col, GREEN, YELLOW, COLOR_END


if bgmi.config.IS_PYTHON3:
    _unicode = str
else:
    _unicode = unicode


def bangumi_calendar(force_update=False, today=False, followed=False, save=True):
    env_columns = get_terminal_col()

    COL = 42

    if env_columns < COL:
        print_warning('terminal window is too small.')
        env_columns = COL

    row = int(env_columns / COL if env_columns / COL <= 3 else 3)

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
        num = COL - 3
        # print('+', '-' * num, '+', '-' * num, '+', '-' * num, '+')
        split = '-' * num + '   '
        print(split * row)

    if today:
        weekday_order = (Bangumi.week[datetime.datetime.today().weekday()], )
    else:
        weekday_order = shift(Bangumi.week, datetime.datetime.today().weekday())

    spacial_append_chars = ['Ⅱ', 'Ⅲ', '♪', 'Δ', '×', '☆', 'é', '·']
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
                space_count = COL - 2 - (full * 2 + half)

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
                    f = map(lambda s: s['name'], Subtitle.get_subtitle(bangumi['subtitle_group'].split(', ')))
                    print(bangumi['name'], ', '.join(f))
                else:
                    print(' ' + bangumi['name'], ' ' * space_count, end='')
                    if (i + 1) % row == 0 or i + 1 == len(weekly_list[weekday.lower()]):
                        print()

            if not followed:
                print()
                # print_line()


def get_response(url, method='GET', **kwargs):
    if os.environ.get('DEBUG'):
        print_info('Request URL: {0}'.format(url))
    try:
        return getattr(requests, method.lower())(url, **kwargs).json()
    except requests.ConnectionError:
        print_error('error: failed to establish a new connection')


def process_subtitle(data):
    '''get subtitle group name from links
    '''
    result = []
    for s in data:
        f = Subtitle(id=s['tag_id'], name=s['name'])
        if not f.select():
            f.save()
        result.append(s['tag_id'])
    return result


def process_name(data):
    lang = 'zh_cn' if LANG not in ('zh_cn', 'zh_tw', 'ja', 'en') else LANG
    return {i['_id']: i['locale'][lang] for i in data}


def parser_bangumi(data, group_by_weekday=True):
    '''match weekly bangumi list from data
    '''

    ids = list(map(lambda b: b['tag_id'], data))
    subtitle = get_response(TEAM_URL, 'POST', json={'tag_ids': ids})
    name = process_name(get_response(NAME_URL, 'POST', json={'_ids': ids}))

    if group_by_weekday:
        weekly_list = defaultdict(list)
    else:
        weekly_list = []

    for bangumi_item in data:
        item = {}
        item['status'] = 0
        item['subtitle_group'] = process_subtitle(subtitle.get(bangumi_item['tag_id'], []))
        item['name'] = name[bangumi_item['tag_id']]
        item['keyword'] = bangumi_item['tag_id']
        item['update_time'] = Bangumi.week[bangumi_item['showOn']-1]
        item['cover'] = bangumi_item['cover']

        if group_by_weekday:
            weekly_list[Bangumi.week[bangumi_item['showOn']-1].lower()].append(item)
        else:
            weekly_list.append(item)

    if not weekly_list:
        bug_report()
    return weekly_list


def fetch(save=False, group_by_weekday=True, status=False):
    response = get_response(FETCH_URL)
    if not response:
        return

    result = parser_bangumi(response, group_by_weekday=group_by_weekday)

    if save:
        if group_by_weekday:
            for i in result.values():
                for bangumi in i:
                    save_data(bangumi)
        else:
            for bangumi in result:
                save_data(bangumi)

    return result


def save_data(data):
    b = Bangumi(**data)
    b.save()


FETCH_EPISODE_ZH = re.compile("[第]\s?(\d{1,2})\s?[話|话|集]")
FETCH_EPISODE_WITH_BRACKETS = re.compile('(?:【|\[)(\d+)\s?(?:END)?(?:】|\])')
FETCH_EPISODE_ONLY_NUM = re.compile('^([\d]{2,})$')
FETCH_EPISODE_RANGE = re.compile('[\d]{2,}\s?-\s?([\d]{2,})')
FETCH_EPISODE = (FETCH_EPISODE_ZH, FETCH_EPISODE_WITH_BRACKETS, FETCH_EPISODE_ONLY_NUM, FETCH_EPISODE_RANGE)


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


def fetch_episode(_id, name='', **kwargs):
    result = []
    response_data = []

    subtitle_group = kwargs.get('subtitle_group', None)
    include = kwargs.get('include', None)
    exclude = kwargs.get('exclude', None)
    regex = kwargs.get('regex', None)
    max_page = kwargs.get('max', int(MAX_PAGE))

    if subtitle_group and subtitle_group.split(', '):
        condition = subtitle_group.split(', ')
        for c in condition:
            data = {'tag_id': [_id, c]}
            response = get_response(DETAIL_URL, 'POST', json=data)
            response_data.extend(response['torrents'])
    else:
        response_data = []
        for i in range(int(max_page)):
            if max_page > 1:
                print_info('Fetch page {0} ...'.format(i + 1))
            response = get_response(DETAIL_URL, 'POST', json={'tag_id': [_id], 'p': i + 1})
            if response:
                response_data.extend(response['torrents'])

    for info in response_data:
        result.append({
            'download': info['magnet'],
            'name': name,
            'subtitle_group': info['team_id'],
            'title': info['title'],
            'episode': parse_episode(info['title']),
            'time': int(time.mktime(datetime.datetime.strptime(info['publish_time'].split('.')[0],
                                                               "%Y-%m-%dT%H:%M:%S").timetuple()))
        })

    if include:
        include_list = map(lambda s: s.strip(), include.split(','))
        result = list(filter(lambda s: True if all(map(lambda t: t in s['title'],
                                                       include_list)) else False, result))

    if exclude:
        exclude_list = map(lambda s: s.strip(), exclude.split(','))
        result = list(filter(lambda s: True if all(map(lambda t: t not in s['title'],
                                                       exclude_list)) else False, result))

    if regex:
        try:
            match = re.compile(regex)
            result = list(filter(lambda s: True if match.findall(s['title']) else False, result))
        except re.error:
            pass

    return result


def get_maximum_episode(bangumi, subtitle=True, ignore_old_row=True, max_page=MAX_PAGE):

    followed_filter_obj = Filter(bangumi_name=bangumi.name)
    followed_filter_obj.select_obj()

    subtitle_group = followed_filter_obj.subtitle if followed_filter_obj and subtitle else None
    include = followed_filter_obj.include if followed_filter_obj and subtitle else None
    exclude = followed_filter_obj.exclude if followed_filter_obj and subtitle else None
    regex = followed_filter_obj.regex if followed_filter_obj and subtitle else None

    data = [i for i in fetch_episode(_id=bangumi.keyword, name=bangumi.name,
                                     subtitle_group=subtitle_group,
                                     include=include, exclude=exclude, regex=regex, max=max_page)
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
