# coding=utf-8
import re
import datetime
import string
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from bgmi.config import FETCH_URL, DETAIL_URL
from bgmi.models import Bangumi, Followed, STATUS_FOLLOWED
from bgmi.utils import print_error, print_warning, print_info


BANGUMI_MATCH = re.compile("(?P<update_time>sun|mon|tue|wed|thu|fri|sat)"
                           "array\.push\(\['.*?','(?P<name>.*?)','(?P<ke"
                           "yword>.*?)','(?P<subtitle_group>.*?)','.*?'"
                           "\]\)")

SUBTITLE_MATCH = re.compile("<a href=\".*?\">(.*?)</a>")


def bangumi_calendar(force_update=False, today=False, followed=False, save=True):
    print_info('Bangumi Weekly Schedule')
    if force_update:
        print_info('fetching bangumi info ...')
        weekly_list = fetch(save=save, status=True)
    else:
        weekly_list = Bangumi.get_all_bangumi(status=STATUS_FOLLOWED if followed else None)

    if not weekly_list:
        if not followed:
            print_warning('warning: no bangumi schedule, fetching ...')
            weekly_list = fetch(save=save)
        else:
            print_warning('you have not subscribe any bangumi')

    def shift(seq, n):
        n = n % len(seq)
        return seq[n:] + seq[:n]

    def print_line():
        print '+', '-' * 29, '+', '-' * 29, '+', '-' * 29, '+'

    if today:
        weekday_order = (Bangumi.week[datetime.datetime.today().weekday()], )
    else:
        weekday_order = shift(Bangumi.week, datetime.datetime.today().weekday())

    spacial_append_chars = ['Ⅱ', 'Ⅲ', '♪']
    spacial_remove_chars = ['Δ', ]
    for index, weekday in enumerate(weekday_order):
        if weekly_list[weekday.lower()]:
            if not followed:
                print ' ' * 46,
            if index == 0:
                print '\033[1;37;40m%s.\033[0m' % weekday,
            else:
                print '\033[1;32m%s.\033[0m' % weekday,
            if not followed:
                print
                print_line()

            for i, bangumi in enumerate(weekly_list[weekday.lower()]):
                if isinstance(bangumi['name'], unicode):
                    bangumi['name'] = bangumi['name'].encode('utf-8')
                half = len(re.findall('[%s]' % string.printable, bangumi['name']))
                full = (len(bangumi['name']) - half) / 3
                space_count = 28 - (full * 2 + half)

                for s in spacial_append_chars:
                    if s in bangumi['name']:
                        space_count += 1

                for s in spacial_remove_chars:
                    if s in bangumi['name']:
                        space_count -= 1
                if bangumi['status'] == STATUS_FOLLOWED:
                    bangumi['name'] = '\033[1;33m%s\033[0m' % bangumi['name']

                if followed:
                    if i > 0:
                        print ' ' * 4,
                    print bangumi['name'], bangumi['subtitle_group']
                else:
                    if (i + 1) % 3 == 1:
                        print '|',
                    print bangumi['name'], ' ' * space_count, '|' if not followed else ' ',
                    if (i + 1) % 3 == 0 or i + 1 == len(weekly_list[weekday.lower()]):
                        print

            if not followed:
                print_line()


def get_response(url):
    try:
        return requests.get(url).content
    except Exception, e:
        print_error('error: %s' % str(e))


def process_subtitle(data):
    '''get subtitle group name from links
    '''
    result = SUBTITLE_MATCH.findall(data)

    # split non-value
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

    return weekly_list


def fetch(save=False, group_by_weekday=True, status=False):
    response = get_response(FETCH_URL)
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


FETCH_EPISODE = re.compile("^[第]?(\d+)]")
FETCH_EPISODE_FALLBACK = re.compile("^(\d+)$")


def parse_episode(data):
    for i in data.split('['):
        match = FETCH_EPISODE.findall(i)
        if match and match[0].isdigit():
            return int(match[0])
    for i in data.split():
        match = FETCH_EPISODE_FALLBACK.findall(i)
        if match and match[0].isdigit():
            return int(match[0])


def fetch_episode(keyword):
    response = get_response(DETAIL_URL + keyword)
    b = BeautifulSoup(response)
    container = b.find('table', attrs={'class': 'tablesorter'})
    result = []
    bangumi_update_info = {}

    for info in container.tbody.find_all('tr'):
        # bangumi_update_info = {}
        for i, detail in enumerate(info.find_all('td')):
            if i == 0:
                bangumi_update_info['time'] = detail.span.text
            if i == 2:
                title = detail.find('a', attrs={'target': '_blank'}).text.strip()
                bangumi_update_info['title'] = title
                bangumi_update_info['episode'] = parse_episode(title)
            if i == 3:
                bangumi_update_info['download'] = detail.find('a').attrs.get('href')
        result.append(bangumi_update_info)

    return bangumi_update_info


def get_maximum_episode(data):
    bangumi = max(data, key=lambda i: i['episode'])
    if bangumi['episode'] is not None:
        return bangumi


if __name__ == '__main__':
    # fetch(save=True, group_by_weekday=False)
    fetch_episode('%E5%B0%8F%E4%B8%B8%E5%AD%90')
    fetch_episode('%E8%81%96%E6%88%B0%E5%88%BB')
