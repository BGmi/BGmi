# coding=utf-8
import os
import sqlite3
from bgmi.command import CommandParser
from bgmi.fetch import fetch, bangumi_calendar
from bgmi.utils import print_warning, print_info, print_success, print_bilibili, print_error
from bgmi.models import Bangumi, Followed, STATUS_FOLLOWED
from bgmi.sql import CREATE_TABLE_BANGUMI, CREATE_TABLE_FOLLOWED


ACTION_FETCH = 'fetch'
ACTION_LIST = 'list'
ACTION_ADD = 'add'
ACTION_DELETE = 'delete'
ACTION_UPDATE = 'update'
ACTION_CAL = 'cal'
ACTIONS = (ACTION_ADD, ACTION_DELETE, ACTION_FETCH, ACTION_LIST, ACTION_UPDATE, ACTION_CAL)


def main():
    c = CommandParser()
    positional = c.add_arg_group('action')
    positional.add_argument('action')

    sub_parser_cal = positional.add_sub_parser('cal')
    sub_parser_cal.add_argument('filter', default='today', choice=('today', 'all', 'followed'))
    sub_parser_cal.add_argument('--today')
    sub_parser_cal.add_argument('--force-update')
    sub_parser_cal.add_argument('--no-save')

    sub_parser_add = positional.add_sub_parser('add')
    sub_parser_add.add_argument('name', arg_type='+', required=True)

    sub_parser_del = positional.add_sub_parser('delete')
    sub_parser_del.add_argument('--name', arg_type='+', mutex='--clear-all')
    sub_parser_del.add_argument('--clear-all')

    ret = c.parse_command()

    # print_bilibili()
    if ret.action not in ACTIONS:
        c.print_help()
        exit(0)

    if ret.action == 'add':
        for bangumi in ret.add.name:
            _ = Bangumi(name=bangumi)
            data = _.select(one=True, fields=['id', 'name', 'update_time'])
            if data:
                f = Followed(bangumi_name=data['name'], episode=0, status=STATUS_FOLLOWED)
                if not f.select():
                    print_success('Bangumi<id: %s, name: %s, update time: %s> followed'
                                  % tuple(data))
                    f.save()
                else:
                    print_warning('Bangumi<id: %s, name: %s, update time: %s> already followed'
                                  % tuple(data))
                # _.update({'status': STATUS_FOLLOWED})

    elif ret.action == 'delete':
        if ret.delete.clear_all:
            if Followed.delete_followed(batch=False):
                print_success('all subscribe had been deleted')
            else:
                print_error('user canceled')
        elif ret.delete.name:
            for name in ret.delete.name:
                followed = Followed(bangumi_name=name)
                if followed.select():
                    followed.delete()
                    print_warning('Bangumi %s has been deleted' % name)
                else:
                    print_error('Bangumi %s not exist' % name, exit_=False)
        else:
            print 'Help Delete'

    elif ret.action in (ACTION_UPDATE, ACTION_FETCH):
        print_info('fetching bangumi data ...')
        if ret.action == ACTION_UPDATE:
            pass
        fetch(save=True, group_by_weekday=False)
        print_success('done')

    elif ret.action == ACTION_CAL:
        force = ret.cal.force_update
        save = not ret.cal.no_save
        today = ret.cal.today
        if ret.cal.filter == 'today':
            bangumi_calendar(force_update=force, today=True, save=save)
        elif ret.cal.filter == 'followed':
            bangumi_calendar(force_update=force, followed=True, today=today, save=save)
        else:
            bangumi_calendar(force_update=force, today=today, save=save)


def init_db():
    conn = sqlite3.connect('bangumi.db')
    conn.execute(CREATE_TABLE_BANGUMI)
    conn.execute(CREATE_TABLE_FOLLOWED)

if __name__ == '__main__':
    if not os.path.exists('bangumi.db'):
        init_db()

    main()
