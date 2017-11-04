# coding=utf-8
from __future__ import print_function, unicode_literals

import datetime
import os
import re
import string

from bgmi.config import write_config
from bgmi.constants import (ACTION_ADD, ACTION_SOURCE, ACTION_DOWNLOAD, ACTION_CONFIG, ACTION_DELETE, ACTION_MARK,
                            ACTION_SEARCH, ACTION_FILTER, ACTION_CAL, ACTION_UPDATE, ACTION_FETCH, ACTION_LIST,
                            DOWNLOAD_CHOICE_LIST_DICT,
                            SPACIAL_APPEND_CHARS, SPACIAL_REMOVE_CHARS)
from bgmi.controllers import (filter_, source,
                              mark, delete, add, search, update, list_)
from bgmi.download import download_prepare, get_download_class
from bgmi.fetch import website
from bgmi.models import Filter, Subtitle, Followed, Bangumi
from bgmi.models import STATUS_FOLLOWED, STATUS_UPDATED
from bgmi.script import ScriptRunner
from bgmi.utils import (GREEN, COLOR_END, get_terminal_col,
                        YELLOW)
from bgmi.utils import print_info, print_warning, print_success, print_error


def source_wrapper(ret):
    result = source(data_source=ret.source)
    globals()["print_{}".format(result['status'])](result['message'])
    return result


def config_wrapper(ret):
    result = write_config(ret.name, ret.value)
    if (not ret.name) and (not ret.value):
        print(result['message'])
    else:
        globals()["print_{}".format(result['status'])](result['message'])


def search_wrapper(ret):
    data = search(keyword=ret.keyword, count=ret.count, regex=ret.regex_filter)

    for i in data:
        print_success(i['title'])
    if ret.download:
        download_prepare(data)


def mark_wrapper(ret):
    result = mark(name=ret.name, episode=ret.episode)
    globals()["print_{}".format(result['status'])](result['message'])


def delete_wrapper(ret):
    if ret.clear_all:
        delete('', clear_all=ret.clear_all, batch=ret.batch)
    else:
        for bangumi_name in ret.name:
            result = delete(name=bangumi_name)
            globals()["print_{}".format(result['status'])](result['message'])


def add_wrapper(ret):
    for bangumi_name in ret.name:
        result = add(name=bangumi_name, episode=ret.episode)
        globals()["print_{}".format(result['status'])](result['message'])


def list_wrapper(*args):
    result = list_()
    print(result['message'])


def cal_wrapper(ret):
    force_update = ret.force_update
    today = ret.today
    save = not ret.no_save
    cover = ret.download_cover

    weekly_list = website.bangumi_calendar(
        force_update=force_update, save=save, cover=cover)

    runner = ScriptRunner()
    patch_list = runner.get_models_dict()
    for i in patch_list:
        weekly_list[i['update_time'].lower()].append(i)

    def shift(seq, n):
        n %= len(seq)
        return seq[n:] + seq[:n]

    if today:
        weekday_order = (Bangumi.week[datetime.datetime.today().weekday()],)
    else:
        weekday_order = shift(Bangumi.week, datetime.datetime.today().weekday())

    env_columns = 42 if os.environ.get(
        'TRAVIS_CI', False) else get_terminal_col()

    col = 42

    if env_columns < col:
        print_warning('terminal window is too small.')
        env_columns = col

    row = int(env_columns / col if env_columns / col <= 3 else 3)

    def print_line():
        num = col - 3
        split = '-' * num + '   '
        print(split * row)

    for index, weekday in enumerate(weekday_order):
        if weekly_list[weekday.lower()]:
            print(
                '%s%s. %s' % (
                    GREEN, weekday if not today else 'Bangumi Schedule for Today (%s)' % weekday, COLOR_END),
                end='')
            print()
            print_line()
            for i, bangumi in enumerate(weekly_list[weekday.lower()]):
                if bangumi['status'] in (STATUS_UPDATED, STATUS_FOLLOWED) and 'episode' in bangumi:
                    bangumi['name'] = '%s(%d)' % (
                        bangumi['name'], bangumi['episode'])

                half = len(re.findall('[%s]' %
                                      string.printable, bangumi['name']))
                full = (len(bangumi['name']) - half)
                space_count = col - 2 - (full * 2 + half)

                for s in SPACIAL_APPEND_CHARS:
                    if s in bangumi['name']:
                        space_count += bangumi['name'].count(s)

                for s in SPACIAL_REMOVE_CHARS:
                    if s in bangumi['name']:
                        space_count -= bangumi['name'].count(s)

                if bangumi['status'] == STATUS_FOLLOWED:
                    bangumi['name'] = '%s%s%s' % (
                        YELLOW, bangumi['name'], COLOR_END)

                if bangumi['status'] == STATUS_UPDATED:
                    bangumi['name'] = '%s%s%s' % (
                        GREEN, bangumi['name'], COLOR_END)
                print(' ' + bangumi['name'], ' ' * space_count, end='')
                if (i + 1) % row == 0 or i + 1 == len(weekly_list[weekday.lower()]):
                    print()
            print()


def filter_wrapper(ret):
    result = filter_(name=ret.name,
                     subtitle=ret.subtitle,
                     include=ret.include,
                     exclude=ret.exclude,
                     regex=ret.regex)
    if 'data' not in result:
        globals()["print_{}".format(result['status'])](result['message'])
    else:
        print_info('Usable subtitle group: {0}'.format(', '.join(result['data']['subtitle_group'])))
        followed_filter_obj = Filter.get(bangumi_name=ret.name)
        print_filter(followed_filter_obj)
    return result['data']


def update_wrapper(ret):
    update(name=ret.name, download=ret.download, not_ignore=ret.not_ignore)


def download_manager(ret):
    if ret.id:
        # 没有入口..
        download_id = ret.id
        status = ret.status
        if download_id is None or status is None:
            print_error('No id or status specified.')
        # download_obj = NeoDownload.get(_id=download_id)
        # if not download_obj:
        #     print_error('Download object does not exist.')
        # print_info('Download Object <{0} - {1}>, Status: {2}'.format(download_obj.name, download_obj.episode,
        #                                                              download_obj.status))
        # download_obj.status = status
        # download_obj.save()
        print_success('Download status has been marked as {0}'.format(
            DOWNLOAD_CHOICE_LIST_DICT.get(int(status))))
    else:
        status = ret.status
        status = int(status) if status is not None else None
        delegate = get_download_class(instance=False)
        delegate.download_status(status=status)


def fetch_(ret):
    try:
        bangumi_obj = Bangumi.get(name=ret.name)
    except Bangumi.DoesNotExist:
        print_error('Bangumi {0} not exist'.format(ret.name))
        return

    try:
        Followed.get(bangumi_name=bangumi_obj.name)
    except Bangumi.DoesNotExist:
        print_error('Bangumi {0} is not followed'.format(ret.name))
        return

    followed_filter_obj = Filter.get(bangumi_name=ret.name)
    print_filter(followed_filter_obj)

    print_info('Fetch bangumi {0} ...'.format(bangumi_obj.name))
    _, data = website.get_maximum_episode(bangumi_obj, ignore_old_row=False if ret.not_ignore else True)

    if not data:
        print_warning('Nothing.')
    for i in data:
        print_success(i['title'])


CONTROLLERS_DICT = {
    ACTION_ADD: add_wrapper,
    ACTION_SOURCE: source_wrapper,
    ACTION_DOWNLOAD: download_manager,
    ACTION_CONFIG: config_wrapper,
    ACTION_DELETE: delete_wrapper,
    ACTION_MARK: mark_wrapper,
    ACTION_SEARCH: search_wrapper,
    ACTION_FILTER: filter_wrapper,
    ACTION_CAL: cal_wrapper,
    ACTION_UPDATE: update_wrapper,
    ACTION_FETCH: fetch_,
    ACTION_LIST: list_wrapper,
}


def controllers(ret):
    func = CONTROLLERS_DICT.get(ret.action, None)
    if not callable(func):
        return
    else:
        return func(ret)


def print_filter(followed_filter_obj):
    print_info('Followed subtitle group: {0}'.format(', '.join(map(lambda s: s['name'], Subtitle.get_subtitle_by_id(
        followed_filter_obj.subtitle.split(', ')))) if followed_filter_obj.subtitle else 'None'))
    print_info('Include keywords: {0}'.format(followed_filter_obj.include))
    print_info('Exclude keywords: {0}'.format(followed_filter_obj.exclude))
    print_info('Regular expression: {0}'.format(followed_filter_obj.regex))
