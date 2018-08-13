# coding=utf-8
import sqlite3

from bgmi.config import DB_PATH, SCRIPT_DB_PATH, BGMI_PATH
from bgmi.utils import print_error
from bgmi.lib.models import Bangumi, Followed, Subtitle, Filter, Download, Scripts

CLEAR_TABLE_ = 'DELETE  FROM {}'


def init_db():
    try:
        # bangumi.db
        conn = sqlite3.connect(DB_PATH)
        conn.close()
        Bangumi.create_table()
        Followed.create_table()
        Download.create_table()
        Filter.create_table()
        Subtitle.create_table()

        # script.db
        conn = sqlite3.connect(SCRIPT_DB_PATH)
        conn.close()
        Scripts.create_table()
    except sqlite3.OperationalError:
        print_error('Open database file failed, path %s is not writable.' % BGMI_PATH)
