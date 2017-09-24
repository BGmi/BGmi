# coding=utf-8
from __future__ import print_function, unicode_literals

import datetime
import os
import re
import string
import time

from bgmi.config import write_config
from bgmi.constants import ACTION_ADD, ACTION_SOURCE, ACTION_DOWNLOAD, ACTION_CONFIG, ACTION_DELETE, ACTION_MARK, \
    ACTION_SEARCH, ACTION_FILTER, ACTION_CAL, ACTION_UPDATE, ACTION_FETCH, ACTION_LIST, DOWNLOAD_CHOICE_LIST_DICT
from bgmi.controllers import filter_, source, \
    mark, delete, add, search, print_filter
from bgmi.download import download_prepare, get_download_class
from bgmi.fetch import website
from bgmi.models import Followed, STATUS_FOLLOWED, Bangumi, STATUS_UPDATED, Download, STATUS_NOT_DOWNLOAD, Filter
from bgmi.script import ScriptRunner
from bgmi.utils import print_success, print_info, print_warning, print_error, GREEN, COLOR_END, get_terminal_col, YELLOW


def source_wrapper(ret):
    return source(source=ret.source)


def config_wrapper(ret):
    result = write_config(ret.name, ret.value)
    if (not ret.name) and (not ret.value):
        print(result['message'])
    else:
        globals()["print_{}".format(result['status'])](result['message'])


def search_wrapper(ret):
    data = search(keyword=ret.keyword, count=ret.count)

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


def cal_wrapper(ret):
    force_update = ret.force_update
    today = ret.today
    save = not ret.no_save
    weekly_list = website.bangumi_calendar(
        force_update=force_update, save=save, cover=True)

    def shift(seq, n):
        n %= len(seq)
        return seq[n:] + seq[:n]

    if today:
        weekday_order = (Bangumi.week[datetime.datetime.today().weekday()],)
    else:
        weekday_order = shift(
            Bangumi.week, datetime.datetime.today().weekday())

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

    spacial_append_chars = ['Ⅱ', 'Ⅲ', '♪', 'Δ', '×', '☆', 'é', '·', '♭']
    spacial_remove_chars = []

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

                for s in spacial_append_chars:
                    if s in bangumi['name']:
                        space_count += 1

                for s in spacial_remove_chars:
                    if s in bangumi['name']:
                        space_count -= 1

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
    data = filter_(name=ret.name,
                   subtitle=ret.subtitle,
                   include=ret.include,
                   exclude=ret.exclude,
                   regex=ret.regex)
    return data


def update(ret):
    ignore = not bool(ret.not_ignore)
    print_info('marking bangumi status ...')
    now = int(time.time())
    for i in Followed.get_all_followed():
        if i['updated_time'] and int(i['updated_time'] + 86400) < now:
            followed_obj = Followed(bangumi_name=i['bangumi_name'])
            followed_obj.status = STATUS_FOLLOWED
            followed_obj.save()

    for script in ScriptRunner().scripts:
        obj = script.Model().obj
        if obj['updated_time'] and int(obj['updated_time'] + 86400) < now:
            obj.status = STATUS_FOLLOWED
            obj.save()

    print_info('updating bangumi data ...')
    website.fetch(save=True, group_by_weekday=False)
    print_info('updating subscriptions ...')
    download_queue = []

    if ret.download:
        if not ret.name:
            print_warning('No specified bangumi, ignore `--download` option')
        if len(ret.name) > 1:
            print_warning(
                'Multiple specified bangumi, ignore `--download` option')

    if not ret.name:
        updated_bangumi_obj = Followed.get_all_followed()
    else:
        updated_bangumi_obj = []
        for i in ret.name:
            f = Followed(bangumi_name=i)
            f.select_obj()
            updated_bangumi_obj.append(f)

    runner = ScriptRunner()
    script_download_queue = runner.run()

    for subscribe in updated_bangumi_obj:
        print_info('fetching %s ...' % subscribe['bangumi_name'])
        bangumi_obj = Bangumi(name=subscribe['bangumi_name'])
        bangumi_obj.select_obj()

        followed_obj = Followed(bangumi_name=subscribe['bangumi_name'])
        followed_obj.select_obj()

        # filter by subtitle group
        if not bangumi_obj or not followed_obj:
            print_error('Bangumi<{0}> does not exist or not been followed.'.format(subscribe['bangumi_name']),
                        exit_=False)
            continue

        episode, all_episode_data = website.get_maximum_episode(
            bangumi=bangumi_obj, ignore_old_row=ignore, max_page=1)

        if (episode.get('episode') > subscribe['episode']) or (len(ret.name) == 1 and ret.download):
            if len(ret.name) == 1 and ret.download:
                episode_range = ret.download
            else:
                episode_range = range(
                    subscribe['episode'] + 1, episode.get('episode', 0) + 1)
                print_success('%s updated, episode: %d' %
                              (subscribe['bangumi_name'], episode['episode']))
                followed_obj.episode = episode['episode']
                followed_obj.status = STATUS_UPDATED
                followed_obj.updated_time = int(time.time())
                followed_obj.save()

            for i in episode_range:
                for epi in all_episode_data:
                    if epi['episode'] == i:
                        download_queue.append(epi)
                        break

    if ret.download is not None:
        download_prepare(download_queue)
        download_prepare(script_download_queue)
        print_info('Re-downloading ...')
        download_prepare(Download.get_all_downloads(
            status=STATUS_NOT_DOWNLOAD))


def list_(ret):
    weekday_order = Bangumi.week
    followed_bangumi = website.followed_bangumi()
    if not followed_bangumi:
        print_warning('you have not subscribed any bangumi')
    else:
        for index, weekday in enumerate(weekday_order):
            if followed_bangumi[weekday.lower()]:
                print('%s%s. %s' % (GREEN, weekday, COLOR_END), end='')
                for i, bangumi in enumerate(followed_bangumi[weekday.lower()]):
                    if bangumi['status'] in (STATUS_UPDATED, STATUS_FOLLOWED) and 'episode' in bangumi:
                        bangumi['name'] = '%s(%d)' % (
                            bangumi['name'], bangumi['episode'])
                    if i > 0:
                        print(' ' * 5, end='')
                    f = map(lambda x: x['name'], bangumi['subtitle_group'])
                    print(bangumi['name'], ', '.join(f))


def fetch_(ret):
    bangumi_obj = Bangumi(name=ret.name)
    bangumi_obj.select_obj()

    followed_obj = Followed(bangumi_name=bangumi_obj.name)
    followed_obj.select_obj()

    followed_filter_obj = Filter(bangumi_name=ret.name)
    followed_filter_obj.select_obj()
    print_filter(followed_filter_obj)

    if bangumi_obj:
        print_info('Fetch bangumi {0} ...'.format(bangumi_obj.name))
        _, data = website.get_maximum_episode(bangumi_obj,
                                              ignore_old_row=False if ret.not_ignore else True)
        if not data:
            print_warning('Nothing.')
        for i in data:
            print_success(i['title'])
    else:
        print_error('Bangumi {0} not exist'.format(ret.name))


def download_manager(ret):
    if ret.id:
        download_id = ret.id
        status = ret.status
        if download_id is None or status is None:
            print_error('No id or status specified.')
        download_obj = Download(_id=download_id)
        download_obj.select_obj()
        if not download_obj:
            print_error('Download object does not exist.')
        print_info('Download Object <{0} - {1}>, Status: {2}'.format(download_obj.name, download_obj.episode,
                                                                     download_obj.status))
        download_obj.status = status
        download_obj.save()
        print_success('Download status has been marked as {0}'.format(
            DOWNLOAD_CHOICE_LIST_DICT.get(int(status))))
    else:
        status = ret.status
        status = int(status) if status is not None else None
        delegate = get_download_class(instance=False)
        delegate.download_status(status=status)


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
    ACTION_UPDATE: update,
    ACTION_FETCH: fetch_,
    ACTION_LIST: list_,
}


def controllers(ret):
    func = CONTROLLERS_DICT.get(ret.action, None)
    if func is None or not callable(func):
        return
    else:
        return func(ret)
