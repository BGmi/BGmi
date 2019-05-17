import sqlite3

import peewee
from playhouse import db_url

from bgmi import config
from bgmi.lib.models import Bangumi, BangumiItem, Download, Followed, Scripts, Subtitle
from bgmi.utils import print_error


def init_db():
    # bangumi.db
    database = db_url.parse(config.DB_URL)
    db_name = database['database']
    schema = config.DB_URL.split(':', 1).pop(0)
    if 'mysql' in schema:
        import pymysql
        try:
            conn = pymysql.connect(
                host=database.get('host'),
                user=database.get('user'),
                password=database.get('passwd'),
            )
        except peewee.InternalError as e:
            print(e.args)
            exit()
            # (1049, "Unknown database 'bgmi'")
        with conn.cursor() as cur:
            cur.execute(
                'CREATE DATABASE IF NOT EXISTS {} default character set utf8mb4 '
                'collate utf8mb4_unicode_ci;'.format(db_name)
            )
    elif 'sqlite' in schema:
        try:
            sqlite3.connect(db_name)
        except sqlite3.OperationalError:
            print_error('Open database file failed, path %s is not writable.' % config.BGMI_PATH)
    else:
        print_error('unsupported database, now only support sqlite and mysql')
        return
    db = db_url.connect(config.DB_URL)
    db.create_tables([
        Bangumi,
        Followed,
        Download,
        Subtitle,
        BangumiItem,
        Scripts,
    ])


if __name__ == '__main__':
    init_db()
