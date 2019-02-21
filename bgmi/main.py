# coding=utf-8

import argparse
import os
import signal

from six import string_types

from bgmi.config import BGMI_PATH
from bgmi.lib.cli import controllers
from bgmi.lib.constants import actions_and_arguments, ACTION_COMPLETE
from bgmi.lib.update import update_database
from bgmi.setup import create_dir, install_crontab
from bgmi.sql import init_db
from bgmi.utils import print_warning, print_error, print_version, check_update, get_web_admin


# global Ctrl-C signal handler
def signal_handler(s, f):  # pragma: no cover
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
            if isinstance(sub_action['dest'], string_types):
                tmp_sub_parser.add_argument(sub_action['dest'], **sub_action['kwargs'])
            if isinstance(sub_action['dest'], list):
                tmp_sub_parser.add_argument(*sub_action['dest'], **sub_action['kwargs'])

    sub_parser.add_parser(ACTION_COMPLETE, help='Gen completion, `eval "$(bgmi complete)"` '
                                                'or `eval "$(bgmi complete|dos2unix)"`')
    # sub_parser_del.add_argument('command', nargs='+', )

    ret = c.parse_args()
    if ret.action == 'install':
        import bgmi.setup

        bgmi.setup.install()
        get_web_admin(method='install')
        init_db()
        raise SystemExit
    elif ret.action == 'upgrade':
        create_dir()
        update_database()
        check_update(mark=False)
    else:
        check_update()
        controllers(ret)


def setup():
    need_to_init = False
    if not os.path.exists(BGMI_PATH):
        need_to_init = True
        print_warning('BGMI_PATH %s does not exist, installing' % BGMI_PATH)

    create_dir()
    if need_to_init:
        init_db()
        install_crontab()


if __name__ == '__main__':
    setup()
    main()
