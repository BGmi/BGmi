# coding=utf-8
import os
import sqlite3
from bgmi.command import CommandParser
from bgmi.fetch import fetch
from bgmi.utils import bangumi_calendar


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
    # positional.add_argument('action')

    sub_parser_cal = positional.add_sub_parser('cal')
    sub_parser_cal.add_argument('filter', choice=('today', 'all', 'followed'))
    sub_parser_cal.add_argument('--force-update')
    sub_parser_cal.add_argument('--no-save')

    ret = c.parse_command()
    if ret.action not in ACTIONS:
        c.print_help()
        exit(0)

    if ret.action == 'fetch':
        fetch()
    elif ret.action == 'add':
        pass
    elif ret.action == 'delete':
        pass
    elif ret.action == 'list':
        pass
    elif ret.action == 'update':
        pass
    elif ret.action == 'cal':
        force = ret.cal.force_update
        save = not ret.cal.no_save
        if ret.cal.filter == 'today':
            bangumi_calendar(force_update=force, today=True, save=save)
        elif ret.cal.filter == 'followed':
            bangumi_calendar(force_update=force, followed=True, save=save)
        else:
            bangumi_calendar(force_update=force, save=save)


def init_db():
    conn = sqlite3.connect('bangumi.db')
    conn.execute('''CREATE TABLE bangumi (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE,
          subtitle_group TEXT NOT NULL,
          update_time DATE NOT NULL,
          status VARCHAR(20) NOT NULL DEFAULT 0
        )
    ''')

    conn.execute('''CREATE TABLE followed (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          bangumi_id INTEGER NOT NULL
        )
    ''')

if __name__ == '__main__':
    if not os.path.exists('bangumi.db'):
        init_db()

    main()
