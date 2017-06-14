# coding=utf-8
from __future__ import print_function, unicode_literals
import os
import sys
import locale
import codecs
import signal
import sqlite3
import platform
import argparse

import bgmi.config
from bgmi.config import BGMI_PATH, DB_PATH
from bgmi.sql import CREATE_TABLE_BANGUMI, CREATE_TABLE_FOLLOWED, CREATE_TABLE_DOWNLOAD, CREATE_TABLE_FOLLOWED_FILTER, \
    CREATE_TABLE_SUBTITLE
from bgmi.utils.utils import print_warning, print_error, print_version, unicodeize, check_update
from bgmi.controllers import controllers
from bgmi.update import update_database
from bgmi.constants import *

# Wrap sys.stdout into a StreamWriter to allow writing unicode.
if bgmi.config.IS_PYTHON3:
    unicode = str
    file_ = sys.stdout.buffer
    sys.stdout = codecs.getwriter(locale.getpreferredencoding())(file_)
else:
    reload(sys)
    sys.setdefaultencoding('utf-8')
    input = raw_input


# global Ctrl-C signal handler
def signal_handler(signal, frame):
    print_error('User aborted, quit')


signal.signal(signal.SIGINT, signal_handler)


def unicode_(s):
    if not bgmi.config.IS_PYTHON3:
        unicode_string = s.decode(sys.getfilesystemencoding())
        return unicode_string
    else:
        return unicode(s)


# main function
def main():
    c = argparse.ArgumentParser()

    c.add_argument('--version', help='Show the version of BGmi.', action='version', version=print_version())

    sub_parser = c.add_subparsers(help='BGmi actions', dest='action')
    sub_parser_add = sub_parser.add_parser(ACTION_ADD, help='Subscribe bangumi.')
    sub_parser_add.add_argument('name', metavar='name', type=unicode_, nargs='+', help='Bangumi name')
    sub_parser_add.add_argument('--episode', metavar='episode', help='Add bangumi and mark it as specified episode.',
                                type=int)
    sub_parser_add.add_argument('--not-ignore', action='store_true',
                                help='Do not ignore the old bangumi detail rows (3 month ago).')

    sub_parser_list = sub_parser.add_parser(ACTION_LIST, help='List subscribed bangumi.')

    sub_parser_filter = sub_parser.add_parser(ACTION_FILTER, help='Set bangumi fetch filter.')
    sub_parser_filter.add_argument('name', metavar='name', type=unicode_, help='Bangumi name to set the filter.')
    sub_parser_filter.add_argument('--subtitle', metavar='subtitle', type=unicode_,
                                   help='Subtitle group name, split by ",".')
    sub_parser_filter.add_argument('--include', metavar='include', type=unicode_,
                                   help='Filter by keywords which in the title, split by ",".')
    sub_parser_filter.add_argument('--exclude', metavar='exclude', type=unicode_,
                                   help='Filter by keywords which not int the title, split by ",".')
    sub_parser_filter.add_argument('--regex', metavar='regex', type=unicode_,
                                   help='Filter by regular expression')

    sub_parser_del = sub_parser.add_parser(ACTION_DELETE, help='Unsubscribe bangumi.')
    sub_parser_del_mutex = sub_parser_del.add_mutually_exclusive_group(required=True)
    sub_parser_del_mutex.add_argument('--name', metavar='name', nargs='+', type=unicode_,
                                      help='Bangumi name to unsubscribe.')
    sub_parser_del_mutex.add_argument('--clear-all', action='store_true',
                                      help='Clear all the subscriptions.')
    sub_parser_del.add_argument('--batch', action='store_true', help='No confirmation.')

    sub_parser_update = sub_parser.add_parser(ACTION_UPDATE, help='Update bangumi calendar and '
                                                                  'subscribed bangumi episode.')
    sub_parser_update.add_argument('name', metavar='name', type=unicode_, nargs='*', help='Update specified bangumi.')
    sub_parser_update.add_argument('--download', action='store',
                                   help='Download specified episode of the bangumi when updated.',
                                   nargs='*', type=int, metavar='episode')
    sub_parser_update.add_argument('--not-ignore', action='store_true',
                                   help='Do not ignore the old bangumi detail rows (3 month ago).')

    sub_parser_cal = sub_parser.add_parser(ACTION_CAL, help='Print bangumi calendar.')
    sub_parser_cal.add_argument('filter', type=unicode_, metavar='filter', choices=FILTER_CHOICES,
                                help='Calendar form filter ({}).'.format(', '.join(FILTER_CHOICES)))
    sub_parser_cal.add_argument('--today', action='store_true', help='Show bangumi calendar for today.')
    sub_parser_cal.add_argument('--force-update', action='store_true',
                                help='Get the newest bangumi calendar from bangumi.moe.')
    sub_parser_cal.add_argument('--no-save', action='store_true',
                                help='Do not save the bangumi data when force update.')

    sub_parser_config = sub_parser.add_parser(ACTION_CONFIG, help='Config BGmi.')
    sub_parser_config.add_argument('name', nargs='?', type=unicode_, help='Config name')
    sub_parser_config.add_argument('value', nargs='?', type=unicode_, help='Config value')

    sub_parser_mark = sub_parser.add_parser(ACTION_MARK, help='Mark bangumi episode.')
    sub_parser_mark.add_argument('name', help='Bangumi name')
    sub_parser_mark.add_argument('episode', help='Bangumi episode', type=int)

    sub_parser_followed = sub_parser.add_parser(ACTION_FOLLOWED, help='Subscribed bangumi manager.')
    sub_parser_followed_mutex = sub_parser_followed.add_mutually_exclusive_group(required=True)
    sub_parser_followed_mutex.add_argument('--list', help='List subscribed bangumi.', action='store_true')
    sub_parser_followed_mutex.add_argument('--mark', help='Specific bangumi name.', dest='name', type=unicode_)
    sub_parser_followed.add_argument('--episode', help='Specifical bangumi episode.', metavar='episode')

    sub_parser_download = sub_parser.add_parser(ACTION_DOWNLOAD, help='Download manager.')
    sub_parser_download.add_argument('--list', help='List download queue.', action='store_true')
    sub_parser_download.add_argument('--mark', help='Mark download status with a specific id.', dest='id', type=int)
    sub_parser_download.add_argument('--status', type=int, help='Download items status (0: not download, 1: '
                                                                'downloading, 2: alrealy downloaded).',
                                     choices=[0, 1, 2])

    sub_parser_fetch = sub_parser.add_parser(ACTION_FETCH, help='Fetch bangumi.')
    sub_parser_fetch.add_argument('name', help='Bangumi name', type=unicode_)
    sub_parser_fetch.add_argument('--not-ignore', action='store_true',
                                  help='Do not ignore the old bangumi detail rows (3 month ago).')

    sub_parser.add_parser('install', help='Install BGmi download delegate.')
    sub_parser.add_parser('upgrade', help='Check update.')

    ret = c.parse_args()

    if ret.action == 'install':
        import bgmi.setup
        bgmi.setup.install()
        raise SystemExit
    elif ret.action == 'upgrade':
        update_database()
        check_update(mark=False)
    else:
        check_update()
        controllers(ret)


def init_db(db_path):
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(CREATE_TABLE_BANGUMI)
        conn.execute(CREATE_TABLE_FOLLOWED)
        conn.execute(CREATE_TABLE_DOWNLOAD)
        conn.execute(CREATE_TABLE_FOLLOWED_FILTER)
        conn.execute(CREATE_TABLE_SUBTITLE)
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
