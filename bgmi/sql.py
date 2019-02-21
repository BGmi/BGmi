# coding=utf-8
import sqlite3

from playhouse import db_url

from bgmi import config
from bgmi.lib.models import Bangumi, Followed, Subtitle, Filter, Download, BangumiItem, BangumiLink, Scripts
from bgmi.utils import print_error


def init_db():
    # bangumi.db
    database = db_url.parse(config.DB_URL)
    schema = config.DB_URL.split(':', 1).pop(0)
    if 'mysql' in schema:
        import pymysql

        conn = pymysql.connect(host=database.get('host'),
                               user=database.get('user'),
                               password=database.get('password'))
        conn.cursor().execute('CREATE DATABASE IF NOT EXISTS {}'.format(database['database']))
        conn.close()

    elif 'sqlite' in schema:
        try:
            sqlite3.connect(database['database'])
        except sqlite3.OperationalError:
            print_error('Open database file failed, path %s is not writable.' % config.BGMI_PATH)
    else:
        print_error('unsupported database, not only support sqlite and mysql')
        return
    db = db_url.connect(config.DB_URL)
    db.create_tables([
        Bangumi,
        Followed,
        Download,
        Filter,
        Subtitle,
        BangumiItem,
        BangumiLink,
        Scripts,
    ])


if __name__ == '__main__':
    init_db()
