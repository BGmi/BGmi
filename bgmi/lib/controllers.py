# coding=utf-8
import os
import time
import warnings

import attr

from bgmi.config import MAX_PAGE, SHOW_WARNING, write_config
from bgmi.lib import models
from bgmi.lib.download import download_prepare
from bgmi.lib.fetch import website
from bgmi.lib.models import (
    Bangumi, BangumiItem, BangumiLink, DoesNotExist, Download, Followed, Subtitle, model_to_dict
)
from bgmi.script import ScriptRunner
from bgmi.utils import (
    COLOR_END, GREEN, logger, normalize_path, print_error, print_info, print_success, print_warning
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
        if SHOW_WARNING:
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

    def print(self):
        if self.message:
            self.print_map.get(self.status, print)(self.message)


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
        result = {'status': 'error', 'message': '{0} not found, please check the name'.format(name)}
        return result
    followed_obj, this_obj_created = Followed.get_or_create(
        bangumi_name=bangumi_obj.name, defaults={'status': Followed.STATUS.FOLLOWED}
    )
    if not this_obj_created:
        if followed_obj.status == Followed.STATUS.FOLLOWED:
            result = {
                'status': 'warning',
                'message': '{0} already followed'.format(bangumi_obj.name),
            }
            return result
        followed_obj.status = Followed.STATUS.FOLLOWED
        followed_obj.save()

    Followed.get_or_create(bangumi_name=bangumi_obj.name)

    bangumi_data, _ = website.get_maximum_episode(bangumi_obj, max_page=MAX_PAGE)
    followed_obj.episode = bangumi_data['episode'] if episode is None else episode
    followed_obj.save()
    result = {'status': 'success', 'message': '{0} has been followed'.format(bangumi_obj.name)}
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
        Followed.get(bangumi_name=bangumi_obj.name)
        name = bangumi_obj.name
    except Bangumi.DoesNotExist:
        return ControllerResult.new_error('Bangumi {0} does not exist.'.format(name))
    except Followed.DoesNotExist:
        return ControllerResult.new_error(
            'Bangumi {name} has not subscribed, try \'bgmi add "{name}"\'.'.format(name=name)
        )

    followed_filter_obj, _ = Followed.get_or_create(bangumi_name=bangumi_obj.name)

    subtitle_list = bangumi_obj.get_subtitle_of_bangumi()
    valid_data_source_list = [
        x.data_source for x in BangumiItem.get_data_source_by_id(bangumi_obj.id)
    ]

    if subtitle_input is not None:
        if subtitle_input == '':
            followed_filter_obj.subtitle = None
        else:
            subtitle_input = [s.strip() for s in subtitle_input.split(',')]
            valid_subtitle_name_list = [x['name'] for x in subtitle_list]
            for bangumi_name in subtitle_input:
                try:
                    Subtitle.get(name=bangumi_name)
                except Subtitle.DoesNotExist:
                    return ControllerResult.new_error(
                        '{} is not a available subtitle_group'.format(bangumi_name),
                        data={
                            'name': bangumi_obj.name,
                            'data_source': valid_data_source_list,
                            'subtitle_group': list({x['name'] for x in subtitle_list}),
                        }
                    )
                if bangumi_name not in valid_subtitle_name_list:
                    return ControllerResult.new_error(
                        '{} is not a available subtitle'.format(bangumi_name),
                        data={
                            'name': bangumi_obj.name,
                            'data_source': valid_data_source_list,
                            'subtitle_group': list({x['name'] for x in subtitle_list}),
                        }
                    )
            followed_filter_obj.subtitle = subtitle_input

    if data_source_input is not None:
        if data_source_input == '':
            followed_filter_obj.data_source = None
        else:
            data_source_input = [s.strip() for s in data_source_input.split(',')]
            for data_source in data_source_input:
                if data_source not in valid_data_source_list:
                    return ControllerResult.new_error(
                        '{} is not a available data source'.format(data_source)
                    )
            followed_filter_obj.data_source = data_source_input

    if include is not None:
        if not include:
            followed_filter_obj.include = None
        else:
            followed_filter_obj.include = [s.strip() for s in include.split(',')]

    if exclude is not None:
        if not exclude:
            followed_filter_obj.exclude = None
        else:
            followed_filter_obj.exclude = [s.strip() for s in exclude.split(',')]

    if regex is not None:
        if not regex:
            followed_filter_obj.regex = ''
        else:
            followed_filter_obj.regex = regex

    followed_filter_obj.save()

    result.data = {
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
    logger.debug('delete %s', name)
    if clear_all:
        if Followed.delete_followed(batch=batch):
            result['status'] = "warning"
            result['message'] = 'all subscriptions have been deleted'
        else:
            print_error('user canceled')
    elif name:
        try:
            followed = Followed.get(bangumi_name=name)
            followed.status = Followed.STATUS.DELETED
            followed.save()
            result['status'] = 'warning'
            result['message'] = 'Bangumi {} has been deleted'.format(name)
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
        followed_obj = Followed.fuzzy_get(bangumi_name=name)
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


def search(keyword, count=MAX_PAGE, regex=None, dupe=False, min_episode=None, max_episode=None):
    try:
        count = int(count)
    except (TypeError, ValueError):
        count = 3
    try:
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
    except Exception as e:
        if os.getenv('DEBUG'):
            raise
        return {
            'status': 'error',
            'message': str(e),
            'options': {
                'keyword': keyword,
                'count': count,
                'regex': regex,
                'dupe': dupe,
                'min_episode': min_episode,
                'max_episode': max_episode,
            },
            'data': [],
        }


def config(name=None, value=None):
    r = write_config(name, value)
    if name == 'ADMIN_TOKEN':
        r['message'] = 'you need to restart your bgmi_http to make new token work'
    return r


def update(name, download=None, not_ignore=False):
    logger.debug('updating bangumi info with args: download: %s', download)
    result = {'status': 'info', 'message': '', 'data': {'updated': [], 'downloaded': []}}

    ignore = not bool(not_ignore)
    print_info('marking bangumi status ...')
    now = int(time.time())

    for i in Followed.get_all_followed():
        if i['updated_time'] and int(i['updated_time'] + 60 * 60 * 24) < now:
            followed_obj = Followed.get(bangumi_name=i['bangumi_name'])
            followed_obj.status = Followed.STATUS.FOLLOWED
            followed_obj.save()

    for script in ScriptRunner().scripts:
        obj = script.Model().obj
        if obj.updated_time and int(obj.updated_time + 60 * 60 * 24) < now:
            obj.status = Followed.STATUS.FOLLOWED
            obj.save()

    print_info('updating subscriptions ...')
    download_queue = []

    if download:
        if not name:
            print_warning('No specified bangumi, ignore `--download` option')
        if len(name) > 1:
            print_warning('Multiple specified bangumi, ignore `--download` option')

    if not name:
        updated_bangumi_obj = Followed.get_all_followed()
    else:
        updated_bangumi_obj = []
        for i in name:
            try:
                f = Followed.get(bangumi_name=i)
                f = model_to_dict(f)
                updated_bangumi_obj.append(f)
            except DoesNotExist:
                print_error('{} is not a followed bangumi'.format(i))

    runner = ScriptRunner()
    script_download_queue = runner.run()

    for subscribe in updated_bangumi_obj:
        print_info('fetching %s ...' % subscribe['bangumi_name'])
        try:
            bangumi_obj = Bangumi.get(name=subscribe['bangumi_name'])
        except Bangumi.DoesNotExist:
            print_error(
                'Bangumi<{0}> does not exists.'.format(subscribe['bangumi_name']), exit_=False
            )
            continue
        try:
            followed_obj = Followed.get(bangumi_name=subscribe['bangumi_name'])
        except Followed.DoesNotExist:
            print_error(
                'Bangumi<{0}> is not followed.'.format(subscribe['bangumi_name']), exit_=False
            )
            continue

        episode, all_episode_data = website.get_maximum_episode(
            bangumi=bangumi_obj, ignore_old_row=ignore, max_page=MAX_PAGE
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
                result['data']['updated'].append({
                    'bangumi': subscribe['bangumi_name'],
                    'episode': episode['episode'],
                })

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
        download_prepare(Download.get_all_downloads(status=Download.STATUS.NOT_DOWNLOAD))

    return result


def status_(name, status=Followed.STATUS.DELETED):
    result = {'status': 'success', 'message': ''}

    if not (Followed.has_status(status) and status):
        result['status'] = 'error'
        result['message'] = 'Invalid status: {0}'.format(status)
        return result

    status = int(status)
    try:
        followed_obj = Followed.get(bangumi_name=name)
    except Followed.DoesNotExist:
        result['status'] = 'error'
        result['message'] = 'Followed<{0}> does not exists'.format(name)
        return result

    followed_obj.status = status
    followed_obj.save()
    result['message'] = 'Followed<{0}> has been marked as status {1}'.format(name, status)
    return result


def unlink(*bangumi_names):
    Bangumi.delete().where(Bangumi.name.in_(bangumi_names)).execute()
    BangumiLink.unlink(*bangumi_names)


def link(*bangumi_names):
    Bangumi.delete().where(Bangumi.name.in_(bangumi_names)).execute()
    BangumiLink.link(*bangumi_names)


def list_():
    result = ControllerResult()
    weekday_order = Bangumi.week
    followed_bangumi = models.get_followed_bangumi()
    script_bangumi = ScriptRunner().get_models_dict()

    if not followed_bangumi and not script_bangumi:
        return ControllerResult.new_warning('you have not subscribed any bangumi')
    for bangumi_list in followed_bangumi.values():
        for bangumi in bangumi_list:
            bangumi['subtitle_group'] = Subtitle.get_subtitle_of_bangumi(bangumi)
    for i in script_bangumi:
        i['subtitle_group'] = [{'name': '<BGmi Script>'}]
        followed_bangumi[i['update_time'].lower()].append(i)

    message = ''

    for weekday in weekday_order:
        if followed_bangumi[weekday.lower()]:
            message += '%s%s. %s' % (GREEN, weekday, COLOR_END)
            for i, bangumi in enumerate(followed_bangumi[weekday.lower()]):
                if bangumi['status'] in (
                    Followed.STATUS.UPDATED, Followed.STATUS.FOLLOWED
                ) and 'episode' in bangumi:
                    bangumi['name'] = '%s(%d)' % (bangumi['name'], bangumi['episode'])
                if i > 0:
                    message += ' ' * 5
                f = [x['name'] for x in bangumi['subtitle_group']]
                message += '%s: %s\n' % (bangumi['name'], ', '.join(f) if f else '<None>')

    result.message = message
    return result


if __name__ == '__main__':
    ee = cal()
    import json

    print(json.dumps(ee))
