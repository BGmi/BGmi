import argparse
import os
import time

import peewee

from bgmi.config import BGMI_PATH
from bgmi.lib import constants
from bgmi.lib.cli import controllers
from bgmi.lib.constants import actions_and_arguments
from bgmi.lib.models import get_kv_storage
from bgmi.lib.update import upgrade_version
from bgmi.setup import create_dir, install_crontab
from bgmi.sql import init_db
from bgmi.utils import (
    check_update, get_web_admin, print_error, print_info, print_version, print_warning
)


def get_arg_parser():
    c = argparse.ArgumentParser()

    c.add_argument(
        '--version', help='Show the version of BGmi.', action='version', version=print_version()
    )

    sub_parser = c.add_subparsers(help='BGmi actions', dest='action')

    for action in actions_and_arguments:
        tmp_sub_parser = sub_parser.add_parser(action['action'], help=action.get('help', ''))
        for sub_action in action.get('arguments', []):
            if isinstance(sub_action['dest'], str):
                tmp_sub_parser.add_argument(sub_action['dest'], **sub_action['kwargs'])
            if isinstance(sub_action['dest'], list):
                tmp_sub_parser.add_argument(*sub_action['dest'], **sub_action['kwargs'])
    return c


# main function
def main(argv=None, program_name='bgmi'):
    c = get_arg_parser()
    c.prog = program_name
    ret = c.parse_args(argv)
    if ret.action == 'install':
        setup()
        import bgmi.setup
        bgmi.setup.install()
        if ret.install_web:
            get_web_admin(method='install')
        else:
            print_info('skip downloading web static files')
        init_db()
        get_kv_storage()[constants.kv.LAST_CHECK_UPDATE_TIME] = int(time.time())
    elif ret.action == 'upgrade':
        create_dir()
        upgrade_version()
        check_update(mark=False)
    else:
        try:
            check_update()
        except peewee.OperationalError:
            if os.getenv('DEBUG'):
                raise
            print_error('call `bgmi install` to install bgmi')

        controllers(ret)


def setup():
    if not os.path.exists(BGMI_PATH):
        print_warning('BGMI_PATH %s does not exist, installing' % BGMI_PATH)

    create_dir()
    install_crontab()


if __name__ == '__main__':
    main()
