import argparse
import os

import peewee

import bgmi
import bgmi.setup
from bgmi.lib.cli import controllers
from bgmi.lib.constants import actions_and_arguments
from bgmi.lib.update import upgrade_version
from bgmi.utils import check_update, print_error, print_version


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
        bgmi.setup.install(ret)

    elif ret.action == 'upgrade':
        bgmi.setup.create_dir()
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
