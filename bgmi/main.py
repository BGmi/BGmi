# coding=utf-8
from __future__ import print_function, unicode_literals
import os
import sqlite3
import signal
import datetime
from bgmi.command import CommandParser
from bgmi.download import download_prepare
from bgmi.fetch import fetch, bangumi_calendar, get_maximum_episode
from bgmi.utils import print_warning, print_info, print_success, print_error, print_version
from bgmi.models import Bangumi, Followed, STATUS_FOLLOWED, STATUS_UPDATED, STATUS_NORMAL
from bgmi.sql import CREATE_TABLE_BANGUMI, CREATE_TABLE_FOLLOWED, CREATE_TABLE_DOWNLOAD
from bgmi.config import BGMI_PATH, DB_PATH, write_config


ACTION_HTTP = 'http'
ACTION_ADD = 'add'
ACTION_DELETE = 'delete'
ACTION_UPDATE = 'update'
ACTION_CAL = 'cal'
ACTION_CONFIG = 'config'
ACTIONS = (ACTION_HTTP, ACTION_ADD, ACTION_DELETE, ACTION_UPDATE, ACTION_CAL, ACTION_CONFIG)

FILTER_CHOICE_TODAY = 'today'
FILTER_CHOICE_ALL = 'all'
FILTER_CHOICE_FOLLOWED = 'followed'
FILTER_CHOICES = (FILTER_CHOICE_ALL, FILTER_CHOICE_FOLLOWED, FILTER_CHOICE_TODAY)


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

    sub_parser_del = action.add_sub_parser(ACTION_DELETE, help='Unsubscribe bangumi.')
    sub_parser_del.add_argument('--name', arg_type='+', mutex='--clear-all', help='Bangumi name to unsubscribe.')
    sub_parser_del.add_argument('--clear-all', help='Clear all the subscriptions.')
    sub_parser_del.add_argument('--batch', help='No confirm.')

    sub_parser_update = action.add_sub_parser(ACTION_UPDATE, help='Update bangumi calendar and '
                                                                  'subscribed bangumi episode.')
    sub_parser_update.add_argument('--download', help='Download the bangumi when updated.')

    sub_parser_cal = action.add_sub_parser(ACTION_CAL, help='Print bangumi calendar.')
    sub_parser_cal.add_argument('filter', default='today', choice=FILTER_CHOICES,
                                help='Calendar form filter %s.' % ', '.join(FILTER_CHOICES))
    sub_parser_cal.add_argument('--today', help='Show bangumi calendar of today.')
    sub_parser_cal.add_argument('--force-update', help='Get the newest bangumi calendar from dmhy.')
    sub_parser_cal.add_argument('--no-save', help='Not save the bangumi data when force update.')

    sub_parser_http = action.add_sub_parser(ACTION_HTTP, help='BGmi HTTP Server.')
    sub_parser_http.add_argument('--port', default='23333', arg_type='1', dest='port',
                                 help='The port of BGmi HTTP Server listened, default 23333.')
    sub_parser_config = action.add_sub_parser(ACTION_CONFIG, help='Config BGmi.')
    sub_parser_config.add_argument('name', help='Config name')
    sub_parser_config.add_argument('value', help='Config value')

    positional = c.add_arg_group('positional')
    positional.add_argument('install', help='Install xunlei-lixian for BGmi.')

    c.add_argument('-h', help='Print help text.')
    c.add_argument('--version', help='Show the version of BGmi.')
    c.add_argument('--debug', help='Enable DEBUG mode.')

    ret = c.parse_command()

    if ret.version:
        print_version()
        raise SystemExit

    if ret.positional.install == 'install':
        import bgmi.setup
        bgmi.setup.install()
        raise SystemExit

    if ret.action == ACTION_HTTP:
        import bgmi.http
        port = ret.action.http.port
        if port.isdigit():
            port = int(port)
        else:
            print_error('Invalid port %s' % port)
        bgmi.http.main(port)

    elif ret.action == ACTION_ADD:
        add(ret)

    elif ret.action == ACTION_DELETE:
        delete(ret)

    elif ret.action == ACTION_UPDATE:
        update(ret)

    elif ret.action == ACTION_CAL:
        cal(ret)
    elif ret.action == ACTION_CONFIG:
        write_config(ret.action.config.name, ret.action.config.value)
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
            if not followed_obj.select():
                ret, _ = get_maximum_episode(keyword=data['keyword'])
                followed_obj.episode = ret['episode']
                followed_obj.save()
                print_success('{0} has followed'.format(bangumi_obj))
            else:
                if followed_obj.status == STATUS_NORMAL:
                    followed_obj.status = STATUS_FOLLOWED
                    followed_obj.save()
                    print_success('{0} has followed'.format(bangumi_obj))
                else:
                    print_warning('{0} already followed'.format(bangumi_obj))
        else:
            print_warning('{0} not found, please check the name'.format(bangumi))


def delete(ret):
    # action delete
    # just delete subscribed bangumi or clear all the subscribed bangumi
    if ret.action.delete.clear_all:
        if Followed.delete_followed(batch=ret.action.delete.batch):
            print_success('all subscribe had been deleted')
        else:
            print_error('user canceled')
    elif ret.action.delete.name:
        for name in ret.action.delete.name:
            followed = Followed(bangumi_name=name)
            if followed.select():
                followed.delete()
                print_warning('Bangumi %s has been deleted' % name)
            else:
                print_error('Bangumi %s not exist' % name, exit_=False)
    else:
        print_warning('Nothing has been done.')


def update(ret):
    print_info('marking bangumi status ...')
    week = Bangumi.week[datetime.datetime.today().weekday()]
    for i in Bangumi.get_all_bangumi(status=STATUS_UPDATED, order=False):
        if i['update_time'] != week:
            _ = Followed(bangumi_name=i['name'])
            _.status = STATUS_FOLLOWED
            _.save()

    print_info('updating bangumi data ...')
    fetch(save=True, group_by_weekday=False)
    print_info('updating subscribe ...')
    download_queue = []
    for subscribe in Followed.get_all_followed():
        print_info('fetching %s ...' % subscribe['bangumi_name'])
        keyword = Bangumi(name=subscribe['bangumi_name']).select(one=True)['keyword']
        episode, all_episode_data = get_maximum_episode(keyword)
        if episode.get('episode') > subscribe['episode']:
            episode_range = range(subscribe['episode'] + 1, episode.get('episode'))
            print_success('%s updated, episode: %d' % (subscribe['bangumi_name'], episode['episode']))
            _ = Followed(bangumi_name=subscribe['bangumi_name'])
            _.episode = episode['episode']
            _.status = STATUS_UPDATED
            _.save()
            download_queue.append(episode)
            for i in episode_range:
                for epi in all_episode_data:
                    if epi['episode'] == i:
                        download_queue.append(epi)
                        break

    if ret.action.update and ret.action.update.download:
        download_prepare(download_queue)


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


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute(CREATE_TABLE_BANGUMI)
    conn.execute(CREATE_TABLE_FOLLOWED)
    conn.execute(CREATE_TABLE_DOWNLOAD)
    conn.commit()
    conn.close()


def setup():
    if not os.path.exists(BGMI_PATH):
        print_error('BGMI_PATH %s not exist, try to reinstall' % BGMI_PATH)

    if not os.path.exists(DB_PATH):
        init_db(DB_PATH)
    main()


if __name__ == '__main__':
    setup()
