# coding=utf-8
from __future__ import print_function, unicode_literals

from bgmi.config import write_config
from bgmi.constants import SUPPORT_WEBSITE
from bgmi.download import download_prepare
from bgmi.fetch import website
from bgmi.models import Bangumi, Filter, Subtitle, STATUS_FOLLOWED
from bgmi.models import Followed
from bgmi.models import (STATUS_NORMAL, DB)
from bgmi.script import ScriptRunner
from bgmi.utils import (print_info, normalize_path)
from bgmi.utils import print_success, print_error


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
    print_info('Followed subtitle group: {0}'.format(', '.join(map(lambda s: s['name'], Subtitle.get_subtitle(
        followed_filter_obj.subtitle.split(', ')))) if followed_filter_obj.subtitle else 'None'))
    print_info('Include keywords: {0}'.format(followed_filter_obj.include))
    print_info('Exclude keywords: {0}'.format(followed_filter_obj.exclude))
    print_info('Regular expression: {0}'.format(followed_filter_obj.regex))


def filter_(name, subtitle=None, include=None, exclude=None, regex=None):
    bangumi_obj = Bangumi(name=name)
    bangumi_obj.select_obj()
    if not bangumi_obj:
        print_error('Bangumi {0} does not exist.'.format(bangumi_obj.name))

    followed_obj = Followed(bangumi_name=bangumi_obj.name)
    followed_obj.select_obj()

    if not followed_obj:
        print_error('Bangumi {name} has not subscribed, try \'bgmi add "{name}"\'.'.format(name=bangumi_obj.name))

    followed_filter_obj = Filter(bangumi_name=name)
    followed_filter_obj.select_obj()

    if not followed_filter_obj:
        followed_filter_obj.save()

    if subtitle is not None:
        subtitle = map(lambda s: s.strip(), subtitle.split(','))
        subtitle = map(lambda s: s['id'], Subtitle.get_subtitle_by_name(subtitle))
        subtitle_list = [s.split('.')[0] for s in bangumi_obj.subtitle_group.split(', ') if '.' in s]
        subtitle_list.extend(bangumi_obj.subtitle_group.split(', '))
        subtitle = filter(lambda s: True if s in subtitle_list else False, subtitle)
        subtitle = ', '.join(subtitle)
        followed_filter_obj.subtitle = subtitle

    if include is not None:
        followed_filter_obj.include = include

    if exclude is not None:
        followed_filter_obj.exclude = exclude

    if regex is not None:
        followed_filter_obj.regex = regex

    followed_filter_obj.save()
    subtitle_list = list(map(lambda s: s['name'], Subtitle.get_subtitle(bangumi_obj.subtitle_group.split(', '))))
    print_info('Usable subtitle group: {0}'.format(', '.join(subtitle)) if subtitle_list else 'None')

    print_filter(followed_filter_obj)
    return {'bangumi_name': name,
            'subtitle_group': list(
                map(lambda s: s['name'], Subtitle.get_subtitle(bangumi_obj.subtitle_group.split(', ')))),
            'include': followed_filter_obj.include,
            'exclude': followed_filter_obj.exclude,
            'regex': followed_filter_obj.regex,
            }


def delete(name='', clear_all=False, batch=False):
    """
    :param name:
    :type name: str
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
            print_success('all subscriptions have been deleted')
            result['status'] = "success"
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
        result['message'] = '{} has been mark as episode: {}'.format(followed_obj, followed_obj.episode)
    else:
        result['status'] = 'info'
        result['message'] = '{}, episode: {}'.format(followed_obj, followed_obj.episode)
    return result


def search(keyword, count=3, dupe=True):
    data = website.search_by_keyword(keyword, count=count)
    if not dupe:
        data = website.remove_duplicated_bangumi(data)

    return data


def source(source):
    result = {}
    if source in list(map(lambda x: x['id'], SUPPORT_WEBSITE)):
        DB.recreate_source_relatively_table()
        write_config('DATA_SOURCE', source)
        print_success('data source switch succeeds')
        from bgmi.fetch import DATA_SOURCE_MAP
        data = DATA_SOURCE_MAP.get(source)().bangumi_calendar(force_update=True)
        result['status'] = 'success'
        result['message'] = 'you have successfully change your data source to {}'.format(source)
        result['data'] = data
    else:
        result['status'] = 'error'
        result['message'] = 'please check input.nata source should be {} or {}'.format(
            *[x['id'] for x in SUPPORT_WEBSITE])
    return result


def config(name, value):
    if name == 'DATA_SOURCE':
        error_message = "you can't change data source in this way. please use bgmi source ${data source } in cli"
        result = {'status': 'error',
                  'message': error_message,
                  'data': write_config()['data']}
        print(error_message)
        return result
    return write_config(name, value)
