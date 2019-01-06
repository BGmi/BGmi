# coding=utf-8
import sqlite3

from bgmi.config import DB_PATH, SCRIPT_DB_PATH, BGMI_PATH
from bgmi.utils import print_error
from bgmi.lib.models import Bangumi, Followed, Subtitle, Filter, Download, Scripts, BangumiItem, BangumiLink


def init_db():
    try:
        # bangumi.db
        sqlite3.connect(DB_PATH).close()
        Bangumi.create_table()
        Followed.create_table()
        Download.create_table()
        Filter.create_table()
        Subtitle.create_table()
        BangumiItem.create_table()
        BangumiLink.create_table()

        # script.db
        sqlite3.connect(SCRIPT_DB_PATH).close()
        Scripts.create_table()
    except sqlite3.OperationalError:
        print_error('Open database file failed, path %s is not writable.' % BGMI_PATH)


if __name__ == '__main__':
    init_db()
