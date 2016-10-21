# coding=utf-8
from __future__ import print_function, unicode_literals
import os
import sys
import locale
import codecs
import signal
import sqlite3
import time
import platform

import bgmi.config
from bgmi.command import CommandParser
from bgmi.config import BGMI_PATH, DB_PATH, write_config
from bgmi.download import download_prepare
from bgmi.fetch import fetch, bangumi_calendar, get_maximum_episode
from bgmi.models import Bangumi, Followed, Download, Filter, STATUS_FOLLOWED, STATUS_UPDATED,\
    STATUS_NORMAL, STATUS_NOT_DOWNLOAD
from bgmi.sql import CREATE_TABLE_BANGUMI, CREATE_TABLE_FOLLOWED, CREATE_TABLE_DOWNLOAD, CREATE_TABLE_FOLLOWED_FILTER
from bgmi.utils.utils import print_warning, print_info, print_success, print_error, print_version
from bgmi.download import get_download_class


# Wrap sys.stdout into a StreamWriter to allow writing unicode.
if bgmi.config.IS_PYTHON3:
    file_ = sys.stdout.buffer
    sys.stdout = codecs.getwriter(locale.getpreferredencoding())(file_)
else:
    reload(sys)
    sys.setdefaultencoding('utf-8')
    input = raw_input


ACTION_ADD = 'add'
ACTION_FETCH = 'fetch'
ACTION_FILTER = 'filter'
ACTION_DELETE = 'delete'
ACTION_UPDATE = 'update'
ACTION_CAL = 'cal'
ACTION_CONFIG = 'config'
ACTION_DOWNLOAD = 'download'
ACTION_FOLLOWED = 'followed'
ACTION_MARK = 'mark'
ACTIONS = (ACTION_ADD, ACTION_DELETE, ACTION_UPDATE, ACTION_CAL,
           ACTION_CONFIG, ACTION_FILTER, ACTION_FETCH, ACTION_DOWNLOAD, ACTION_FOLLOWED,
           ACTION_MARK, )

FILTER_CHOICE_TODAY = 'today'
FILTER_CHOICE_ALL = 'all'
FILTER_CHOICE_FOLLOWED = 'followed'
FILTER_CHOICES = (FILTER_CHOICE_ALL, FILTER_CHOICE_FOLLOWED, FILTER_CHOICE_TODAY)


DOWNLOAD_ACTION_LIST = 'list'
DOWNLOAD_ACTION_MARK = 'mark'
DOWNLOAD_ACTION = (DOWNLOAD_ACTION_LIST, DOWNLOAD_ACTION_MARK)


DOWNLOAD_CHOICE_LIST_ALL = 'all'
DOWNLOAD_CHOICE_LIST_NOT_DOWNLOAD = 'not_downloaded'
DOWNLOAD_CHOICE_LIST_DOWNLOADING = 'downloading'
DOWNLOAD_CHOICE_LIST_DOWNLOADED = 'downloaded'
DOWNLOAD_CHOICE_LIST_DICT = {
    None: DOWNLOAD_CHOICE_LIST_ALL,
    0: DOWNLOAD_CHOICE_LIST_NOT_DOWNLOAD,
    1: DOWNLOAD_CHOICE_LIST_DOWNLOADING,
    2: DOWNLOAD_CHOICE_LIST_DOWNLOADED,
}

DOWNLOAD_CHOICE = (DOWNLOAD_CHOICE_LIST_ALL, DOWNLOAD_CHOICE_LIST_DOWNLOADED,
                   DOWNLOAD_CHOICE_LIST_DOWNLOADING, DOWNLOAD_CHOICE_LIST_NOT_DOWNLOAD)

FOLLOWED_ACTION_LIST = 'list'
FOLLOWED_ACTION_MARK = 'mark'
FOLLOWED_CHOICE = (FOLLOWED_ACTION_LIST, FOLLOWED_ACTION_MARK)


# global Ctrl-C signal handler
def signal_handler(signal, frame):
    print_error('User aborted, quit')
signal.signal(signal.SIGINT, signal_handler)


# main function
def main():
    c = CommandParser()
    action = c.add_arg_group('action')

    sub_parser_add = action.add_sub_parser(ACTION_ADD, help='Subscribe bangumi.')
    sub_parser_add.add_argument('name', arg_type='+', required=True, help='Bangumi name to subscribe.')

    sub_parser_filter = action.add_sub_parser(ACTION_FILTER, help='Set bangumi fetch filter.')
    sub_parser_filter.add_argument('name', required=True, help='Bangumi name to set the filter.')
    sub_parser_filter.add_argument('--subtitle', arg_type='1', help='Subtitle group name, split by ",".')
    sub_parser_filter.add_argument('--include', arg_type='1',
                                   help='Filter by keywords which in the title, split by ",".')
    sub_parser_filter.add_argument('--exclude', arg_type='1',
                                   help='Filter by keywords which not int the title, split by ",".')
    # sub_parser_filter.add_argument('--remove', help='Remove subtitle group filter.')
    # sub_parser_filter.add_argument('--remove-all', help='Remove all the subtitle group filter.', mutex='--remove')

    sub_parser_del = action.add_sub_parser(ACTION_DELETE, help='Unsubscribe bangumi.')
    sub_parser_del.add_argument('--name', arg_type='+', mutex='--clear-all', help='Bangumi name to unsubscribe.')
    sub_parser_del.add_argument('--clear-all', help='Clear all the subscriptions.')
    sub_parser_del.add_argument('--batch', help='No confirmation.')

    sub_parser_fetch = action.add_sub_parser(ACTION_FETCH, help='Fetch a specific bangumi.')
    sub_parser_fetch.add_argument('name', help='Bangumi name to fetch.', required=True)
    sub_parser_fetch.add_argument('--not-ignore', help='Do not ignore the old bangumi detail rows (3 month ago).')

    sub_parser_update = action.add_sub_parser(ACTION_UPDATE, help='Update bangumi calendar and '
                                                                  'subscribed bangumi episode.')
    sub_parser_update.add_argument('--name', arg_type='+', help='Update specified bangumi.')
    sub_parser_update.add_argument('--download', help='Download the bangumi when updated.')
    sub_parser_update.add_argument('--not-ignore', help='Do not ignore the old bangumi detail rows (3 month ago).')

    sub_parser_cal = action.add_sub_parser(ACTION_CAL, help='Print bangumi calendar.')
    sub_parser_cal.add_argument('filter', default='today', choice=FILTER_CHOICES,
                                help='Calendar form filter %s.' % ', '.join(FILTER_CHOICES))
    sub_parser_cal.add_argument('--today', help='Show bangumi calendar for today.')
    sub_parser_cal.add_argument('--force-update', help='Get the newest bangumi calendar from dmhy.')
    sub_parser_cal.add_argument('--no-save', help='Do not save the bangumi data when force update.')

    sub_parser_config = action.add_sub_parser(ACTION_CONFIG, help='Config BGmi.')
    sub_parser_config.add_argument('name', help='Config name')
    sub_parser_config.add_argument('value', help='Config value')

    sub_parser_followed = action.add_sub_parser(ACTION_FOLLOWED, help='Subscribed bangumi manager.')
    sub_parser_followed.add_sub_parser('list', help='List subscribed bangumi.')
    followed_mark = sub_parser_followed.add_sub_parser('mark', help='Mark specific bangumi\'s episode.')
    followed_mark.add_argument('name', help='Bangumi name.', required=True)
    followed_mark.add_argument('episode', help='Bangumi episode.')

    sub_parser_mark = action.add_sub_parser(ACTION_MARK, help='Mark subscribed bangumi status.')
    sub_parser_mark.add_argument('name', help='Bangumi name.', required=True)
    sub_parser_mark.add_argument('episode', help='Bangumi episode.')

    sub_parser_download = action.add_sub_parser(ACTION_DOWNLOAD, help='Download manager.')
    download_list = sub_parser_download.add_sub_parser('list', help='List download queue.')
    download_list.add_argument('status', help='Download status: 0, 1, 2', choice=(0, 1, 2, None))

    download_mark = sub_parser_download.add_sub_parser('mark', help='Mark download status with a specific id.')
    download_mark.add_argument('id', help='Download id')
    download_mark.add_argument('status', help='Status will be marked', choice=(0, 1, 2))

    positional = c.add_arg_group('positional')
    positional.add_argument('install', help='Install xunlei-lixian for BGmi.')

    c.add_argument('-h / --help', help='Print help text.')
    c.add_argument('--version', help='Show the version of BGmi.')

    ret = c.parse_command()

    if ret.version:
        print_version()
        raise SystemExit

    if ret.positional.install == 'install':
        import bgmi.setup
        bgmi.setup.install()
        raise SystemExit

    elif ret.action == ACTION_ADD:
        add(ret)

    elif ret.action == ACTION_FILTER:
        filter_(ret)

    elif ret.action == ACTION_FETCH:
        bangumi_obj = Bangumi(name=ret.action.fetch.name)
        bangumi_obj.select_obj()

        followed_obj = Followed(bangumi_name=bangumi_obj.name)
        followed_obj.select_obj()

        if bangumi_obj:
            print_info('Fetch bangumi {0} ...'.format(bangumi_obj.name))
            _, data = get_maximum_episode(bangumi_obj,
                                          ignore_old_row=False if ret.action.fetch.not_ignore else True)
            if not data:
                print_warning('Nothing.')
            for i in data:
                print_success(i['title'])

        else:
            print_error('Bangumi {0} not exist'.format(ret.action.fetch.name))

    elif ret.action == ACTION_DELETE:
        delete(ret)

    elif ret.action == ACTION_UPDATE:
        update(ret)

    elif ret.action == ACTION_CAL:
        cal(ret)

    elif ret.action == ACTION_CONFIG:
        write_config(ret.action.config.name, ret.action.config.value)

    elif ret.action == ACTION_FOLLOWED:
        if not ret.action.followed == 'mark' and not ret.action.followed.list:
            c.print_help()
        else:
            followed(ret)

    elif ret.action == ACTION_MARK:
        mark(ret)

    elif ret.action == ACTION_DOWNLOAD:
        if ret.action.download in DOWNLOAD_ACTION:
            download_manager(ret)
        else:
            c.print_help()
    else:
        c.print_help()


def add(ret):
    # action add
    # add bangumi by a list of bangumi name
    if not Bangumi.get_all_bangumi():
        print_warning('No bangumi data in database, fetching...')
        update(ret)

    for bangumi in ret.action.add.name:
        bangumi_obj = Bangumi(name=bangumi)
        data = bangumi_obj.select(one=True, fields=['id', 'name', 'keyword'])
        if data:
            followed_obj = Followed(bangumi_name=data['name'], status=STATUS_FOLLOWED)
            followed_obj.select_obj()
            if not followed_obj or followed_obj.status == STATUS_NORMAL:
                if not followed_obj:
                    ret, _ = get_maximum_episode(bangumi_obj, subtitle=False)
                    followed_obj.episode = ret['episode']
                    followed_obj.save()
                else:
                    followed_obj.status = STATUS_FOLLOWED
                    followed_obj.save()
                print_success('{0} has been followed'.format(bangumi_obj))
            else:
                print_warning('{0} already followed'.format(bangumi_obj))

        else:
            print_error('{0} not found, please check the name'.format(bangumi))


def filter_(ret):
    bangumi_obj = Bangumi(name=ret.action.filter.name)
    bangumi_obj.select_obj()
    if not bangumi_obj:
        print_error('Bangumi {0} does not exist.'.format(bangumi_obj.name))

    followed_obj = Followed(bangumi_name=bangumi_obj.name)
    followed_obj.select_obj()

    if not followed_obj:
        print_error('Bangumi {0} has not subscribed, try \'bgmi add "{1}"\'.'.format(bangumi_obj.name,
                                                                                     bangumi_obj.name))

    subtitle = ret.action.filter.subtitle
    include = ret.action.filter.include
    exclude = ret.action.filter.exclude

    followed_filter_obj = Filter(bangumi_name=bangumi_obj.name)
    followed_filter_obj.select_obj()

    if not followed_filter_obj:
        followed_filter_obj.save()

    if subtitle is not None:
        subtitle = map(lambda s: s.strip(), subtitle.split(','))
        subtitle = filter(lambda s: True if s in bangumi_obj.subtitle_group.split(', ') else False, subtitle)
        subtitle = ', '.join(subtitle)
        followed_filter_obj.subtitle = subtitle

    if include is not None:
        followed_filter_obj.include = include

    if exclude is not None:
        followed_filter_obj.exclude = exclude

    followed_filter_obj.save()

    print_info('Usable subtitle group: {0}'.format(bangumi_obj.subtitle_group))
    print_success('Added subtitle group: {0}'.format(followed_filter_obj.subtitle))
    print_success('Include keywords: {0}'.format(followed_filter_obj.include))
    print_success('Exclude keywords: {0}'.format(followed_filter_obj.exclude))


def delete(ret):
    # action delete
    # just delete subscribed bangumi or clear all the subscribed bangumi
    if ret.action.delete.clear_all:
        if Followed.delete_followed(batch=ret.action.delete.batch):
            print_success('all subscriptions have been deleted')
        else:
            print_error('user canceled')
    elif ret.action.delete.name:
        for name in ret.action.delete.name:
            followed = Followed(bangumi_name=name)
            if followed.select():
                followed.delete()
                print_warning('Bangumi %s has been deleted' % name)
            else:
                print_error('Bangumi %s does not exist' % name, exit_=False)
    else:
        print_warning('Nothing has been done.')


def update(ret):
    ignore = False if ret.action.update.not_ignore else True
    print_info('marking bangumi status ...')
    now = int(time.time())
    for i in Followed.get_all_followed():
        if i['updated_time'] and int(i['updated_time'] + 86400) < now:
            followed_obj = Followed(bangumi_name=i['bangumi_name'])
            followed_obj.status = STATUS_FOLLOWED
            followed_obj.save()

    print_info('updating bangumi data ...')
    fetch(save=True, group_by_weekday=False)
    print_info('updating subscriptions ...')
    download_queue = []

    if ret.action.update.name is None:
        updated_bangumi_obj = Followed.get_all_followed()
    else:
        updated_bangumi_obj = []
        for i in ret.action.update.name:
            f = Followed(bangumi_name=i)
            f.select_obj()
            updated_bangumi_obj.append(f)

    for subscribe in updated_bangumi_obj:
        print_info('fetching %s ...' % subscribe['bangumi_name'])
        bangumi_obj = Bangumi(name=subscribe['bangumi_name'])
        bangumi_obj.select_obj()

        # filter by subtitle group
        if not bangumi_obj:
            print_error('The bangumi {0} you subscribed does not exists ..'.format(subscribe['bangumi_name']),
                        exit_=False)
            continue

        episode, all_episode_data = get_maximum_episode(bangumi=bangumi_obj, ignore_old_row=ignore)
        if episode.get('episode') > subscribe['episode']:
            episode_range = range(subscribe['episode'] + 1, episode.get('episode'))
            print_success('%s updated, episode: %d' % (subscribe['bangumi_name'], episode['episode']))
            _ = Followed(bangumi_name=subscribe['bangumi_name'])
            _.episode = episode['episode']
            _.status = STATUS_UPDATED
            _.updated_time = int(time.time())
            _.save()
            download_queue.append(episode)
            for i in episode_range:
                for epi in all_episode_data:
                    if epi['episode'] == i:
                        download_queue.append(epi)
                        break

    if ret.action.update and ret.action.update.download:
        download_prepare(download_queue)
        print_info('Re-downloading ...')
        download_prepare(Download.get_all_downloads(status=STATUS_NOT_DOWNLOAD))


def cal(ret):
    force = ret.action.cal.force_update
    save = not ret.action.cal.no_save
    today = ret.action.cal.today
    if ret.action.cal.filter == FILTER_CHOICE_TODAY:
        bangumi_calendar(force_update=force, today=True, save=save)
    elif ret.action.cal.filter == FILTER_CHOICE_FOLLOWED:
        bangumi_calendar(force_update=force, followed=True, today=today, save=save)
    else:
        # fallback
        bangumi_calendar(force_update=force, today=today, save=save)


def download_manager(ret):
    print_info('Download status value: Not Downloaded: 0 / Downloading: 1 / Downloaded: 2\n', indicator=False)

    if ret.action.download == DOWNLOAD_ACTION_LIST:
        status = ret.action.download.list.status
        status = int(status) if status is not None else None
        delegate = get_download_class(instance=False)
        delegate.download_status(status=status)

    elif ret.action.download == DOWNLOAD_ACTION_MARK:
        download_id = ret.action.download.mark.id
        status = ret.action.download.mark.status
        if not download_id or not status:
            print_error('No id or status specified.')
        download_obj = Download(_id=download_id)
        download_obj.select_obj()
        if not download_obj:
            print_error('Download object does not exist.')
        print_info('Download Object <{0} - {1}>, Status: {2}'.format(download_obj.name, download_obj.episode,
                                                                     download_obj.status))
        download_obj.status = status
        download_obj.save()
        print_success('Download status has been marked as {0}'.format(DOWNLOAD_CHOICE_LIST_DICT.get(int(status))))


def mark(ret):
    name = ret.action.mark.name
    episode = ret.action.mark.episode
    followed_obj = Followed(bangumi_name=name)
    followed_obj.select_obj()

    if not followed_obj:
        print_error('Subscribe <%s> does not exist.' % name)

    if episode:
        followed_obj.episode = episode
        followed_obj.save()
        print_success('%s has been mark as episode: %s' % (followed_obj, followed_obj.episode))
    else:
        print_info('%s, episode: %s' % (followed_obj, followed_obj.episode))


def followed(ret):
    if ret.action.followed == FOLLOWED_ACTION_MARK:
        print_warning('Warning: bgmi followed mark is deprecated, please use bgmi mark instead.')
        ret.action.mark = ret.action.followed.mark
        mark(ret)
    else:
        print_warning('Warning: bgmi followed list is deprecated, please use bgmi cal followed instead.')
        bangumi_calendar(force_update=False, followed=True, save=False)


def init_db(db_path):
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(CREATE_TABLE_BANGUMI)
        conn.execute(CREATE_TABLE_FOLLOWED)
        conn.execute(CREATE_TABLE_DOWNLOAD)
        conn.execute(CREATE_TABLE_FOLLOWED_FILTER)
        conn.commit()
        conn.close()
    except sqlite3.OperationalError:
        print_error('Open database file failed, path %s is not writable.' % BGMI_PATH)


def setup():
    if not os.path.exists(BGMI_PATH):
        print_warning('BGMI_PATH %s does not exist, installing' % BGMI_PATH)
        from bgmi.setup import create_dir, install_crontab
        create_dir()
        if not platform.system() == 'Windows':
            # if not input('Do you want to install a crontab to auto-download bangumi?(Y/n): ') == 'n':
            install_crontab()

    # if not os.path.exists(DB_PATH):
    init_db(DB_PATH)
    main()


if __name__ == '__main__':
    setup()
