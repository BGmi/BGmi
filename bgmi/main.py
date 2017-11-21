# coding=utf-8
from __future__ import print_function, unicode_literals

import argparse
import os
import signal
import sqlite3

from bgmi.cli import controllers
from bgmi.config import BGMI_PATH, DB_PATH, SCRIPT_DB_PATH
from bgmi.constants import actions_and_arguments, ACTION_COMPLETE
from bgmi.setup import create_dir, install_crontab
from bgmi.sql import (CREATE_TABLE_BANGUMI, CREATE_TABLE_FOLLOWED, CREATE_TABLE_DOWNLOAD, CREATE_TABLE_FOLLOWED_FILTER,
                      CREATE_TABLE_SUBTITLE, CREATE_TABLE_SCRIPT)
from bgmi.update import update_database
from bgmi.utils import print_warning, print_error, print_version, check_update, get_web_admin


# global Ctrl-C signal handler
def signal_handler(signal, frame):  # pragma: no cover
    print_error('User aborted, quit')


signal.signal(signal.SIGINT, signal_handler)


# main function
def main():
    setup()
    c = argparse.ArgumentParser()

    c.add_argument('--version', help='Show the version of BGmi.', action='version', version=print_version())

    sub_parser = c.add_subparsers(help='BGmi actions', dest='action')

    for action in actions_and_arguments:
        tmp_sub_parser = sub_parser.add_parser(action['action'], help=action.get('help', ''))
        for sub_action in action.get('arguments', []):
            tmp_sub_parser.add_argument(sub_action['dest'], **sub_action['kwargs'])

    sub_parser_del = sub_parser.add_parser(ACTION_COMPLETE, help='Gen completion, `eval "$(bgmi complete)"` or `eval "$(bgmi complete|dos2unix)"`')
    # sub_parser_del.add_argument('command', nargs='+', )

    ret = c.parse_args()
    if ret.action == 'install':
        import bgmi.setup

        bgmi.setup.install()
        get_web_admin(method='install')

        raise SystemExit
    elif ret.action == 'upgrade':
        create_dir()
        update_database()
        check_update(mark=False)
    else:
        check_update()
        controllers(ret)


def init_db():
    try:
        # bangumi.db
        conn = sqlite3.connect(DB_PATH)
        conn.execute(CREATE_TABLE_BANGUMI)
        conn.execute(CREATE_TABLE_FOLLOWED)
        conn.execute(CREATE_TABLE_DOWNLOAD)
        conn.execute(CREATE_TABLE_FOLLOWED_FILTER)
        conn.execute(CREATE_TABLE_SUBTITLE)
        conn.commit()
        conn.close()

        # script.db
        conn = sqlite3.connect(SCRIPT_DB_PATH)
        conn.execute(CREATE_TABLE_SCRIPT)
        conn.commit()
        conn.close()
    except sqlite3.OperationalError:
        print_error('Open database file failed, path %s is not writable.' % BGMI_PATH)


def setup():
    need_to_init = False
    if not os.path.exists(BGMI_PATH):
        need_to_init = True
        print_warning('BGMI_PATH %s does not exist, installing' % BGMI_PATH)

    create_dir()
    init_db()
    if need_to_init:
        install_crontab()


if __name__ == '__main__':
    setup()
    main()
