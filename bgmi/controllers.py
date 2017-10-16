# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import time

from bgmi.config import write_config
from bgmi.constants import SUPPORT_WEBSITE
from bgmi.download import download_prepare
from bgmi.fetch import website
from bgmi.models import (Bangumi, Filter, Subtitle, Download,
                         STATUS_FOLLOWED, STATUS_UPDATED, STATUS_NOT_DOWNLOAD, FOLLOWED_STATUS)
from bgmi.models import Followed
from bgmi.models import (STATUS_NORMAL, DB)
from bgmi.script import ScriptRunner
from bgmi.utils import print_info, normalize_path, print_warning, print_success, print_error, GREEN, COLOR_END


def add(name, episode=None):
    """
    ret.name :str
    """
    # action add
    # add bangumi by a list of bangumi name
    # result = {}
    if not Bangumi.get_all_bangumi():
        website.fetch(save=True, group_by_weekday=False)

    bangumi_obj = Bangumi(name=name)
    data = bangumi_obj.select(one=True, fields=['id', 'name', 'keyword'])
    if data:
        followed_obj = Followed(bangumi_name=data['name'], status=STATUS_FOLLOWED)
        followed_obj.select_obj()
        f, if_this_object_created = Filter.get_or_create(bangumi_name=name)
        if not followed_obj or followed_obj.status == STATUS_NORMAL:
            if not followed_obj:
                bangumi_data, _ = website.get_maximum_episode(bangumi_obj, subtitle=False, max_page=1)
                followed_obj.episode = bangumi_data['episode'] if episode is None else episode
                followed_obj.save()
            else:
                followed_obj.status = STATUS_FOLLOWED
                followed_obj.save()
            result = {'status': 'success', 'message': '{0} has been followed'.format(bangumi_obj)}
        else:
            result = {'status': 'warning', 'message': '{0} already followed'.format(bangumi_obj)}
    else:
        result = {'status': 'error',
                  'message': '{0} not found, please check the name'.format(name)}
    return result


def print_filter(followed_filter_obj):
    print_info('Followed subtitle group: {0}'.format(', '.join(map(lambda s: s['name'], Subtitle.get_subtitle_by_id(
        followed_filter_obj.subtitle.split(', ')))) if followed_filter_obj.subtitle else 'None'))
    print_info('Include keywords: {0}'.format(followed_filter_obj.include))
    print_info('Exclude keywords: {0}'.format(followed_filter_obj.exclude))
    print_info('Regular expression: {0}'.format(followed_filter_obj.regex))


def filter_(name, subtitle=None, include=None, exclude=None, regex=None):
    result = {'status': 'success', 'message': ''}
    bangumi_obj = Bangumi(name=name)
    bangumi_obj.select_obj()
    if not bangumi_obj:
        result['status'] = 'error'
        result['message'] = 'Bangumi {0} does not exist.'.format(bangumi_obj.name)
        return result

    followed_obj = Followed(bangumi_name=bangumi_obj.name)
    followed_obj.select_obj()

    if not followed_obj:
        result['status'] = 'error'
        result['message'] = 'Bangumi {name} has not subscribed, try \'bgmi add "{name}"\'.' \
            .format(name=bangumi_obj.name)
        return result

    followed_filter_obj = Filter.get(bangumi_name=name)

    if not followed_filter_obj:
        followed_filter_obj.save()

    if subtitle is not None:
        subtitle = map(lambda s: s.strip(), subtitle.split(','))
        subtitle = map(lambda s: s['id'], Subtitle.get_subtitle_by_name(subtitle))
        subtitle_list = [s.split('.')[0] for s in bangumi_obj.subtitle_group.split(', ') if '.' in s]
        subtitle_list.extend(bangumi_obj.subtitle_group.split(', '))
        subtitle = filter(lambda s: s in subtitle_list, subtitle)
        subtitle = ', '.join(subtitle)
        followed_filter_obj.subtitle = subtitle

    if include is not None:
        followed_filter_obj.include = include

    if exclude is not None:
        followed_filter_obj.exclude = exclude

    if regex is not None:
        followed_filter_obj.regex = regex

    followed_filter_obj.save()
    subtitle_list = list(map(lambda s: s['name'],
                             Subtitle.get_subtitle_by_id(bangumi_obj.subtitle_group.split(', '))))
    print_info('Usable subtitle group: {0}'.format(', '.join(subtitle_list) if subtitle_list else 'None'))

    print_filter(followed_filter_obj)
    result['data'] = {
        'name': name,
        'subtitle_group': list(map(
            lambda s: s['name'],
            Subtitle.get_subtitle_by_id(bangumi_obj.subtitle_group.split(', ')))),
        'followed': list(map(lambda s: s['name'], Subtitle.get_subtitle_by_id(followed_filter_obj.subtitle.split(', ')))
                         if followed_filter_obj.subtitle else []),
        'include': followed_filter_obj.include,
        'exclude': followed_filter_obj.exclude,
        'regex': followed_filter_obj.regex,
    }
    return result


def delete(name='', clear_all=False, batch=False):
    """
    :param name:
    :type name: unicode
    :param clear_all:
    :type clear_all: bool
    :param batch:
    :type batch: bool
    :return:
    """
    # action delete
    # just delete subscribed bangumi or clear all the subscribed bangumi
    result = {}
    if clear_all:
        if Followed.delete_followed(batch=batch):
            result['status'] = "warning"
            result['message'] = 'all subscriptions have been deleted'
        else:
            print_error('user canceled')
    elif name:
        followed = Followed(bangumi_name=name)
        if followed.select():
            followed.delete()
            result['status'] = 'warning'
            result['message'] = 'Bangumi {} has been deleted'.format(name)
        else:
            result['status'] = 'error'
            result['message'] = 'Bangumi %s does not exist' % name
    else:
        result['status'] = 'warning'
        result['message'] = 'Nothing has been done.'
    return result


def cal(force_update=False, save=False):
    weekly_list = website.bangumi_calendar(force_update=force_update, save=save)
    # for web api
    r = weekly_list
    for day, value in weekly_list.items():
        for index, bangumi in enumerate(value):
            bangumi['cover'] = normalize_path(bangumi['cover'])
            if isinstance(bangumi['subtitle_group'], list):
                subtitle_group = list(map(lambda x: {'name': x['name'], 'id': x['id']},
                                          Subtitle.get_subtitle_by_id(
                                              bangumi['subtitle_group'])))
            else:
                subtitle_group = list(map(lambda x: {'name': x['name'], 'id': x['id']},
                                          Subtitle.get_subtitle_by_id(
                                              bangumi['subtitle_group'].split(', ' ''))))

            r[day][index]['subtitle_group'] = subtitle_group
    return r


def download(name, title, episode, download_url):
    my_dict = {
        'name': name,
        'title': title,
        'episode': episode,
        'download': download_url,
    }
    download_prepare(my_dict)


def mark(name, episode):
    """

    :param name: name of the bangumi you want to mark
    :type name: str
    :param episode: bangumi episode you want to mark
    :type episode: int
    :return: result
    :rtype: dict[status: str,message: str]
    """
    result = {}
    followed_obj = Followed(bangumi_name=name)
    followed_obj.select_obj()

    runner = ScriptRunner()

    if not followed_obj:
        followed_obj = runner.get_model(name)

    if not followed_obj:
        result['status'] = 'error'
        result['message'] = 'Subscribe or Script <{}> does not exist.'.format(name)
        return result

    if episode is not None:
        followed_obj.episode = episode
        followed_obj.save()
        result['status'] = 'success'
        result['message'] = '{} has been mark as episode: {}'.format(name, episode)
    else:  # episode is None
        result['status'] = 'info'
        result['message'] = '{}, episode: {}'.format(name, followed_obj.episode)
    return result


def search(keyword, count=3, dupe=True):
    data = website.search_by_keyword(keyword, count=count)
    if not dupe:
        data = website.remove_duplicated_bangumi(data)

    return data


def source(data_source):
    result = {}
    if data_source in list(map(lambda x: x['id'], SUPPORT_WEBSITE)):
        DB.recreate_source_relatively_table()
        write_config('DATA_SOURCE', data_source)
        print_success('data source switch succeeds')
        from bgmi.fetch import DATA_SOURCE_MAP
        data = DATA_SOURCE_MAP.get(data_source)().bangumi_calendar(force_update=True)
        result['status'] = 'success'
        result['message'] = 'you have successfully change your data source to {}'.format(data_source)
        result['data'] = data
    else:
        result['status'] = 'error'
        result['message'] = 'please check input.nata source should be {} or {}'.format(
            *[x['id'] for x in SUPPORT_WEBSITE])
    return result


def config(name, value):
    if name == 'DATA_SOURCE':
        error_message = "you can't change data source in this way. please use bgmi source ${data source} in cli"
        result = {'status': 'error',
                  'message': error_message,
                  'data': write_config()['data']}
        return result
    r = write_config(name, value)
    if name == 'ADMIN_TOKEN':
        r['message'] = 'you need to restart your bgmi_http to make new token work'
    return r


def update(name, download=None, not_ignore=False):
    result = {'status': 'info', 'message': '', 'data': {'updated': [], 'downloaded': []}}

    ignore = not bool(not_ignore)
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

    if download:
        if not name:
            print_warning('No specified bangumi, ignore `--download` option')
        if len(name) > 1:
            print_warning(
                'Multiple specified bangumi, ignore `--download` option')

    if not name:
        updated_bangumi_obj = Followed.get_all_followed()
    else:
        updated_bangumi_obj = []
        for i in name:
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

        if (episode.get('episode') > subscribe['episode']) or (len(name) == 1 and download):
            if len(name) == 1 and download:
                episode_range = download
            else:
                episode_range = range(
                    subscribe['episode'] + 1, episode.get('episode', 0) + 1)
                print_success('%s updated, episode: %d' %
                              (subscribe['bangumi_name'], episode['episode']))
                followed_obj.episode = episode['episode']
                followed_obj.status = STATUS_UPDATED
                followed_obj.updated_time = int(time.time())
                followed_obj.save()
                result['data']['updated'].append({'bangumi': subscribe['bangumi_name'],
                                                  'episode': episode['episode']})

            for i in episode_range:
                for epi in all_episode_data:
                    if epi['episode'] == i:
                        download_queue.append(epi)
                        break

    if download is not None:
        result['data']['downloaded'] = download_queue
        download_prepare(download_queue)
        download_prepare(script_download_queue)
        print_info('Re-downloading ...')
        download_prepare(Download.get_all_downloads(
            status=STATUS_NOT_DOWNLOAD))

    return result


def status_(name, status=STATUS_NORMAL):
    result = {'status': 'success', 'message': ''}

    if not status in FOLLOWED_STATUS or not status:
        result['status'] = 'error'
        result['message'] = 'Invalid status: {0}'.format(status)
        return result

    status = int(status)
    followed_obj = Followed(bangumi_name=name)
    followed_obj.select_obj()

    if not followed_obj:
        result['status'] = 'error'
        result['message'] = 'Followed<{0}> does not exists'.format(name)
        return result

    followed_obj.status = status
    followed_obj.save()
    result['message'] = 'Followed<{0}> has been marked as status {1}'.format(name, status)
    return result


def list_():
    result = {}
    weekday_order = Bangumi.week
    followed_bangumi = website.followed_bangumi()
    if not followed_bangumi:
        result['status'] = 'warning'
        result['message'] = 'you have not subscribed any bangumi'
    else:
        result['status'] = 'info'
        result['message'] = ''
        for index, weekday in enumerate(weekday_order):
            if followed_bangumi[weekday.lower()]:
                result['message'] += '%s%s. %s' % (GREEN, weekday, COLOR_END)
                for i, bangumi in enumerate(followed_bangumi[weekday.lower()]):
                    if bangumi['status'] in (STATUS_UPDATED, STATUS_FOLLOWED) and 'episode' in bangumi:
                        bangumi['name'] = '%s(%d)' % (
                            bangumi['name'], bangumi['episode'])
                    if i > 0:
                        result['message'] += ' ' * 5
                    f = map(lambda x: x['name'], bangumi['subtitle_group'])
                    result['message'] += '%s: %s\n' % (bangumi['name'], ', '.join(f) if f else '<None>')
    return result


def fetch_(ret):
    bangumi_obj = Bangumi.get(name=ret.name)
    # bangumi_obj.select_obj()

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
