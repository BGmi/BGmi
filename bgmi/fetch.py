# coding=utf-8
import re
import datetime
import string
import requests
from collections import defaultdict
from bgmi.config import FETCH_URL
from bgmi.models import Bangumi, STATUS_FOLLOWED
from bgmi.utils import print_error, print_warning, print_info


BANGUMI_MATCH = re.compile("(?P<update_time>sun|mon|tue|wed|thu|fri|sat)"
                           "array\.push\(\['.*?','(?P<name>.*?)','(?P<ke"
                           "yword>.*?)','(?P<subtitle_group>.*?)','.*?'"
                           "\]\)")

SUBTITLE_MATCH = re.compile("<a href=\".*?\">(.*?)</a>")


def bangumi_calendar(force_update=False, today=False, followed=False, save=True):
    if force_update:
        print_info('fetching bangumi info ...')
        weekly_list = fetch(save=save)
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

    if today:
        weekday_order = (Bangumi.week[datetime.datetime.today().weekday()], )
    else:
        weekday_order = shift(Bangumi.week, datetime.datetime.today().weekday())

    spacial_append_chars = ['Ⅱ', 'Ⅲ', '♪']
    spacial_remove_chars = ['Δ', ]
    for index, weekday in enumerate(weekday_order):
        if weekly_list[weekday.lower()]:
            if index == 0:
                print '\033[1;37;42m%s.\033[0m' % weekday,
            else:
                print '\033[1;32m%s.\033[0m' % weekday,
            if not followed:
                print
                print '-' * 29, '+', '-' * 29, '+', '-' * 29, '+'

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
                if bangumi['status'] == str(STATUS_FOLLOWED):
                    bangumi['name'] = '\033[1;33m%s\033[0m' % bangumi['name']

                if followed:
                    if i > 0:
                        print ' ' * 4,
                    print bangumi['name'], bangumi['subtitle_group']
                else:
                    print bangumi['name'], ' ' * space_count, '|' if not followed else ' ',

                    if (i + 1) % 3 == 0:
                        print

            if not followed:
                print '\n'


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


def parser_bangumi(data, group_by_weekday=True):
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
        if group_by_weekday:
            weekly_list[bangumi_item['update_time']].append(bangumi_item)
        else:
            weekly_list.append(bangumi_item)

    return weekly_list


def fetch(save=False, group_by_weekday=True):
    response = get_response(FETCH_URL)
    result = parser_bangumi(response, group_by_weekday=group_by_weekday)
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


if __name__ == '__main__':
    fetch(save=True, group_by_weekday=False)
