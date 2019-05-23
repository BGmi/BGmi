import time
import warnings
from operator import itemgetter
from typing import Mapping

import attr

from bgmi import config
from bgmi.lib import models
from bgmi.lib.download import download_prepare
from bgmi.lib.fetch import website
from bgmi.lib.models import (
    Bangumi, BangumiItem, DoesNotExist, Download, Followed, Subtitle, model_to_dict
)
from bgmi.lib.models._tables import split_str_to_list
from bgmi.logger import logger
from bgmi.script import ScriptRunner
from bgmi.utils import (
    COLOR_END, GREEN, normalize_path, parallel, print_error, print_info, print_success,
    print_warning
)


@attr.s
class ControllerResult:
    success = 'success'
    warning = 'warning'
    error = 'error'

    status = attr.ib(
        type=str,
        default=success,
        validator=attr.validators.in_([success, warning, error]),
    )
    message = attr.ib(type=str, default='')
    data = attr.ib(factory=dict)

    def __getitem__(self, item):
        if config.SHOW_WARNING:
            warnings.warn("don't use ControllerResult as dict")
        _data = {
            'status': self.status,
            'message': self.message,
            'data': self.data,
        }
        v = _data.get(item, KeyError)
        if v == KeyError:
            raise KeyError(item)
        return v

    get = __getitem__

    def __setitem__(self, key, value):
        if key in ['status', 'message', 'data']:
            setattr(self, key, value)
        else:
            raise KeyError('ControllerResponse can\'t set {}'.format(key))

    @classmethod
    def from_dict(cls, d) -> 'ControllerResult':
        return cls(**d)

    @classmethod
    def new_error(cls, message, **kwargs):
        return cls(status=cls.error, message=message, **kwargs)

    @classmethod
    def new_warning(cls, message, **kwargs):
        return cls(status=cls.warning, message=message, **kwargs)

    def __contains__(self, item):
        return item in ['status', 'message', 'data']

    print_map = {
        success: print_info,
        warning: print_warning,
        error: print_error,
    }

    def print(self, indicator=False):
        if self.message:
            self.print_map.get(self.status, print)(self.message, indicator=indicator)


def add(name, episode=None):
    """
    ret.name :str
    """
    # action add
    # add bangumi by a list of bangumi name
    # result = {}
    logger.debug('add name: %s episode: %s', name, episode)
    if not Bangumi.get_updating_bangumi():
        website.fetch(save=True, group_by_weekday=False)

    try:
        bangumi_obj = Bangumi.fuzzy_get(name=name)
    except Bangumi.DoesNotExist:
        result = {'status': 'error', 'message': '{} not found, please check the name'.format(name)}
        return result
    followed_obj, this_obj_created = Followed.get_or_create(
        bangumi_id=bangumi_obj.id, defaults={'status': Followed.STATUS.FOLLOWED}
    )
    if not this_obj_created:
        if followed_obj.status == Followed.STATUS.FOLLOWED:
            result = {
                'status': 'warning',
                'message': '{} already followed'.format(bangumi_obj.name),
            }
            return result
        followed_obj.status = Followed.STATUS.FOLLOWED
        followed_obj.save()

    Followed.get_or_create(bangumi_id=bangumi_obj.id)

    bangumi_data, _ = website.get_maximum_episode(bangumi_obj, max_page=config.MAX_PAGE)
    followed_obj.episode = bangumi_data['episode'] if episode is None else episode
    followed_obj.save()
    result = {'status': 'success', 'message': '{} has been followed'.format(bangumi_obj.name)}
    logger.debug(result)
    return result


def filter_(
    name,
    subtitle_input=None,
    data_source_input=None,
    include=None,
    exclude=None,
    regex=None,
) -> ControllerResult:
    result = ControllerResult()
    try:
        bangumi_obj = Bangumi.fuzzy_get(name=name)
        Followed.get(bangumi_id=bangumi_obj.id)
        name = bangumi_obj.name
    except Bangumi.DoesNotExist:
        return ControllerResult.new_error('Bangumi {} does not exist.'.format(name))
    except Followed.DoesNotExist:
        return ControllerResult.new_error(
            'Bangumi {name} has not subscribed, try \'bgmi add "{name}"\'.'.format(name=name)
        )

    followed_filter_obj, _ = Followed.get_or_create(bangumi_id=bangumi_obj.id)  # type: Followed
    subtitle_list = [
        x for x in bangumi_obj.get_subtitle_of_bangumi()
        if x['name'] not in config.DISABLED_DATA_SOURCE
    ]
    valid_data_source_list = [
        x.data_source
        for x in BangumiItem.get_data_source_by_id(bangumi_obj.id)
        if x.data_source not in config.DISABLED_DATA_SOURCE
    ]

    if subtitle_input:
        subtitle_input = split_str_to_list(subtitle_input)
        valid_subtitle_name_list = [x['name'] for x in subtitle_list]
        for subtitle_name in subtitle_input:
            try:
                Subtitle.get(name=subtitle_name)
            except Subtitle.DoesNotExist:
                return ControllerResult.new_error(
                    '{} is not a available subtitle_group'.format(subtitle_name),
                    data={
                        'name': bangumi_obj.name,
                        'data_source': valid_data_source_list,
                        'subtitle_group': list({x['name'] for x in subtitle_list}),
                    }
                )
            if subtitle_name not in valid_subtitle_name_list:
                return ControllerResult.new_error(
                    '{} is not a available subtitle'.format(subtitle_name),
                    data={
                        'name': bangumi_obj.name,
                        'data_source': valid_data_source_list,
                        'subtitle_group': list({x['name'] for x in subtitle_list}),
                    }
                )
        followed_filter_obj.subtitle = ','.join(subtitle_input)

    if data_source_input:
        data_source_input = split_str_to_list(data_source_input)
        for data_source in data_source_input:
            if data_source not in valid_data_source_list:
                return ControllerResult.new_error(
                    '{} is not a available data source'.format(data_source)
                )
        followed_filter_obj.data_source = ','.join(data_source_input)

    if include:
        followed_filter_obj.include = include

    if exclude:
        followed_filter_obj.exclude = exclude

    if regex:
        followed_filter_obj.regex = regex

    followed_filter_obj.save()

    result.data = {
        'obj': followed_filter_obj,
        'name': bangumi_obj.name,
        'data_source': valid_data_source_list,
        'subtitle_group': list({x['name'] for x in subtitle_list}),
        'followed': followed_filter_obj.subtitle,
        'followed_data_source': followed_filter_obj.data_source,
        'include': followed_filter_obj.include,
        'exclude': followed_filter_obj.exclude,
        'regex': followed_filter_obj.regex,
    }
    logger.debug(result)
    return result


def delete_(name='', clear_all=False, batch=False):
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
    logger.debug('delete %s', name)
    if clear_all:
        if Followed.delete_followed(batch=batch):
            result['status'] = 'warning'
            result['message'] = 'all subscriptions have been deleted'
        else:
            print_error('user canceled')
    elif name:
        try:
            bangumi = Bangumi.get(name=name)
            followed = Followed.get(bangumi_id=bangumi.id)
            followed.status = Followed.STATUS.DELETED
            followed.save()
            result['status'] = 'warning'
            result['message'] = 'Bangumi {} has been deleted'.format(name)
        except Bangumi.DoesNotExist:
            result['status'] = 'error'
            result['message'] = 'Bangumi {} does not exist'.format(name)
        except Followed.DoesNotExist:
            result['status'] = 'error'
            result['message'] = 'Bangumi %s does not exist' % name
    else:
        result['status'] = 'warning'
        result['message'] = 'Nothing has been done.'
    logger.debug(result)
    return result


def cal():
    logger.debug('controllers cal')
    weekly_list = website.bangumi_calendar()
    runner = ScriptRunner()
    patch_list = runner.get_models_dict()
    for i in patch_list:
        weekly_list[i['update_time'].lower()].append(i)
    logger.debug(weekly_list)

    # for web api, return all subtitle group info
    r = weekly_list
    for value in weekly_list.values():
        for bangumi in value:
            bangumi['cover'] = normalize_path(bangumi['cover'])
    logger.debug(r)
    return r


def download_(name, title, episode, download_url):
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
    try:
        bangumi_obj = Bangumi.fuzzy_get(name=name)
        name = bangumi_obj.name
    except Bangumi.DoesNotExist:
        runner = ScriptRunner()
        followed_obj = runner.get_model(name)
        if not followed_obj:
            result['status'] = 'error'
            result['message'] = 'Subscribe or Script <{}> does not exist.'.format(name)
            return result

    try:
        followed_obj = Followed.get_by_name(bangumi_name=name)
    except Followed.DoesNotExist:
        runner = ScriptRunner()
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


def search(
    keyword,
    count=config.MAX_PAGE,
    regex=None,
    dupe=False,
    min_episode=None,
    max_episode=None,
):
    try:
        count = int(count)
    except (TypeError, ValueError):
        count = 3
    data = website.search_by_keyword(keyword, count=count)
    data = Followed(regex=regex).apply_regex(data)
    if min_episode is not None:
        data = [x for x in data if x['episode'] >= min_episode]
    if max_episode is not None:
        data = [x for x in data if x['episode'] <= max_episode]
    if not dupe:
        data = website.Utils.remove_duplicated_episode_bangumi(data)
    data.sort(key=lambda x: x['episode'])
    if data:
        if data[0]['episode'] == 0:
            data.pop(0)
    return {
        'status': 'success',
        'message': '',
        'options': {
            'keyword': keyword,
            'count': count,
            'regex': regex,
            'dupe': dupe,
            'min_episode': min_episode,
            'max_episode': max_episode,
        },
        'data': data,
    }


def config_(name=None, value=None):
    if not name:
        r = config.print_config()
    elif not value:
        r = config.print_config_key(name)
    else:
        r = config.write_config(name, value)
    return ControllerResult.from_dict(r)


def title_to_weight(title: str, weight: Mapping = None) -> int:
    """
    if ``KEYWORDS_WIGHTS`` is {'a':1,'b':2}

    Args:
        weight: a map from keyword to weight, all values should be int
        title: title of

    Returns:

    """
    if weight is None:
        weight = config.KEYWORDS_WEIGHT

    count = 0
    for key, value in weight.items():
        if key in title:
            count += value
    return count


def update_single_bangumi(subscribe, name, ignore, download):
    updated = []
    download_queue = []
    print_info('fetching %s ...' % subscribe['bangumi_name'])
    try:
        bangumi_obj = Bangumi.get(name=subscribe['bangumi_name'])
        followed_obj = Followed.get(bangumi_id=bangumi_obj.id)
    except Bangumi.DoesNotExist:
        print_error('Bangumi<{}> does not exists.'.format(subscribe['bangumi_name']), exit_=False)
        return [], []
    except Followed.DoesNotExist:
        print_error('Bangumi<{}> is not followed.'.format(subscribe['bangumi_name']), exit_=False)
        return [], []

    episode, all_episode_data = website.get_maximum_episode(
        bangumi=bangumi_obj, ignore_old_row=ignore, max_page=config.MAX_PAGE
    )
    all_episode_data = sorted(
        all_episode_data,
        key=lambda x: title_to_weight(x['title']),
        reverse=True,
    )
    if (episode.get('episode') > subscribe['episode']) or (len(name) == 1 and download):
        if len(name) == 1 and download:
            episode_range = download
        else:
            episode_range = range(subscribe['episode'] + 1, episode.get('episode', 0) + 1)
            print_success(
                '%s updated, episode: %d' % (subscribe['bangumi_name'], episode['episode'])
            )
            followed_obj.episode = episode['episode']
            followed_obj.status = Followed.STATUS.UPDATED
            followed_obj.updated_time = int(time.time())
            followed_obj.save()
            updated.append({
                'bangumi': subscribe['bangumi_name'],
                'episode': episode['episode'],
            })

        for i in episode_range:
            for epi in all_episode_data:
                if epi['episode'] == i:
                    download_queue.append(epi)
                    break

    return updated, download_queue


def update(name, download=None, not_ignore=False):
    """

    Args:
        name: bangumi names to download
        download: episode to download
        not_ignore: don't ignore old bangumi

    Returns:

    """
    logger.debug('updating bangumi info with args: download: %s', download)
    result = {'status': 'info', 'message': '', 'data': {'updated': [], 'downloaded': []}}

    print_info('marking bangumi status ...')
    now = int(time.time())

    for i in Followed.get_all_followed():
        ids = []
        if i['updated_time'] and int(i['updated_time'] + 60 * 60 * 24) < now:
            ids.append(i['bangumi_id'])
        Followed.update(status=Followed.STATUS.FOLLOWED).where(
            Followed.bangumi_id.in_(ids)
        ).execute()

    for script in ScriptRunner().scripts:
        obj = script.Model().obj
        if obj.updated_time and int(obj.updated_time + 60 * 60 * 24) < now:
            obj.status = Followed.STATUS.FOLLOWED
            obj.save()

    print_info('updating subscriptions ...')

    if not name:
        updated_bangumi_obj = Followed.get_all_followed()
    else:
        updated_bangumi_obj = []
        for i in name:
            try:
                f = Followed.get_by_name(bangumi_name=i)
                f = model_to_dict(f)
                f['bangumi_name'] = i
                updated_bangumi_obj.append(f)
            except DoesNotExist:
                print_error('{} is not a followed bangumi'.format(i))

    runner = ScriptRunner()
    script_download_queue = runner.run()

    res = parallel(
        update_single_bangumi,
        ((x, name, not bool(not_ignore), download) for x in updated_bangumi_obj)
    )
    result['data']['updated'] = sum(map(itemgetter(0), res), [])
    download_queue = sum(map(itemgetter(1), res), [])

    if download is not None:
        result['data']['downloaded'] = download_queue
        download_prepare(download_queue)
        download_prepare(script_download_queue)
        print_info('Re-downloading ...')
        download_prepare(Download.get_all_downloads(status=Download.STATUS.NOT_DOWNLOAD))

    return result


def status_(name, status=Followed.STATUS.DELETED):
    result = {'status': 'success', 'message': ''}

    if not (Followed.has_status(status) and status):
        result['status'] = 'error'
        result['message'] = 'Invalid status: {}'.format(status)
        return result

    status = int(status)
    try:
        followed_obj = Followed.get_by_name(bangumi_name=name)
    except Followed.DoesNotExist:
        result['status'] = 'error'
        result['message'] = 'Followed<{}> does not exists'.format(name)
        return result

    followed_obj.status = status
    followed_obj.save()
    result['message'] = 'Followed<{}> has been marked as status {}'.format(name, status)
    return result


def list_():
    result = ControllerResult()
    weekday_order = Bangumi.week
    followed_bangumi = models.get_followed_bangumi()
    script_bangumi = ScriptRunner().get_models_dict()

    if not followed_bangumi and not script_bangumi:
        return ControllerResult.new_warning('you have not subscribed any bangumi')
    for bangumi_list in followed_bangumi.values():
        for bangumi in bangumi_list:
            bangumi['subtitle_group'] = [
                x for x in Subtitle.get_subtitle_of_bangumi(bangumi)
                if x['name'] not in config.DISABLED_DATA_SOURCE
            ]
    for i in script_bangumi:
        i['subtitle_group'] = [{'name': '<BGmi Script>'}]
        followed_bangumi[i['update_time'].lower()].append(i)

    message = ''

    for weekday in weekday_order:
        if followed_bangumi[weekday.lower()]:
            message += '{}{}. {}'.format(GREEN, weekday, COLOR_END)
            for i, bangumi in enumerate(followed_bangumi[weekday.lower()]):
                if bangumi['status'] in (
                    Followed.STATUS.UPDATED, Followed.STATUS.FOLLOWED
                ) and 'episode' in bangumi:
                    bangumi['name'] = '%s(%d)' % (bangumi['name'], bangumi['episode'])
                if i > 0:
                    message += ' ' * 5
                f = [x['name'] for x in bangumi['subtitle_group']]
                message += '{}: {}\n'.format(bangumi['name'], ', '.join(f) if f else '<None>')

    result.message = message
    return result
