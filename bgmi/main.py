# coding=utf-8

import argparse
import os
import signal

import peewee

from bgmi.config import BGMI_PATH
from bgmi.lib.cli import controllers
from bgmi.lib.constants import actions_and_arguments
from bgmi.lib.update import upgrade_version
from bgmi.setup import create_dir, install_crontab
from bgmi.sql import init_db
from bgmi.utils import print_warning, print_error, print_version, check_update, get_web_admin


# global Ctrl-C signal handler
def signal_handler(s, h):  # pragma: no cover # pylint: disable=W0613

    print_error('User aborted, quit')


signal.signal(signal.SIGINT, signal_handler)

# main function


def main(program_name='bgmi'):
    c = argparse.ArgumentParser(prog=program_name)

    c.add_argument('--version',
                   help='Show the version of BGmi.',
                   action='version',
                   version=print_version())

    sub_parser = c.add_subparsers(help='BGmi actions', dest='action')

    for action in actions_and_arguments:
        tmp_sub_parser = sub_parser.add_parser(action['action'], help=action.get('help', ''))
        for sub_action in action.get('arguments', []):
            if isinstance(sub_action['dest'], str):
                tmp_sub_parser.add_argument(sub_action['dest'], **sub_action['kwargs'])
            if isinstance(sub_action['dest'], list):
                tmp_sub_parser.add_argument(*sub_action['dest'], **sub_action['kwargs'])

    ret = c.parse_args()
    if ret.action == 'install':
        setup()
        import bgmi.setup
        bgmi.setup.install()
        get_web_admin(method='install')
        init_db()
        raise SystemExit
    elif ret.action == 'upgrade':
        create_dir()
        upgrade_version()
        check_update(mark=False)
    else:
        try:
            check_update()
        except peewee.OperationalError:
            print_error('call `bgmi install` to install bgmi')

        controllers(ret)


def setup():
    if not os.path.exists(BGMI_PATH):
        print_warning('BGMI_PATH %s does not exist, installing' % BGMI_PATH)

    create_dir()
    install_crontab()


if __name__ == '__main__':
    setup()
    main()
