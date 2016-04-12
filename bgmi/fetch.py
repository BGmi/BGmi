# coding=utf-8
import re
import requests
from collections import defaultdict
from bgmi.config import FETCH_URL
from bgmi.models import Bangumi


BANGUMI_MATCH = re.compile("(?P<update_time>sun|mon|tue|wed|thu|fri|sat)"
                           "array\.push\(\['.*?','(?P<name>.*?)','(?P<ke"
                           "yword>.*?)','(?P<subtitle_group>.*?)','.*?'"
                           "\]\)")

SUBTITLE_MATCH = re.compile("<a href=\".*?\">(.*?)</a>")


def get_response(url):
    return requests.get(url).content


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
        for bangumi in parser_bangumi(response, group_by_weekday=False):
            save_data(bangumi)
    return result


def save_data(data):
    b = Bangumi(**data)
    b.save()


if __name__ == '__main__':
    fetch(save=True, group_by_weekday=False)
