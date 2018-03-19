# coding=utf-8
import sqlite3

from bgmi.config import DB_PATH, SCRIPT_DB_PATH, BGMI_PATH
from bgmi.utils import print_error

CREATE_TABLE_BANGUMI = '''CREATE TABLE IF NOT EXISTS bangumi (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE,
          subtitle_group TEXT NOT NULL,
          keyword TEXT,
          update_time CHAR(5) NOT NULL,
          cover TEXT,
          status INTEGER DEFAULT 0
        )'''

CREATE_TABLE_FOLLOWED = '''CREATE TABLE IF NOT EXISTS followed (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          bangumi_name TEXT NOT NULL UNIQUE,
          episode INTEGER DEFAULT 0,
          status INTEGER DEFAULT 1,
          updated_time INTEGER DEFAULT 0
        )'''

CREATE_TABLE_DOWNLOAD = '''CREATE TABLE IF NOT EXISTS download (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          title TEXT NOT NULL,
          episode INTEGER DEFAULT 0,
          download TEXT,
          status INTEGER DEFAULT 0
        )'''

CREATE_TABLE_FOLLOWED_FILTER = '''CREATE TABLE IF NOT EXISTS filter (
          id INTEGER PRIMARY KEY  AUTOINCREMENT,
          bangumi_name TEXT  UNIQUE NOT NULL,
          subtitle TEXT,
          include TEXT,
          exclude TEXT,
          regex TEXT
        )'''

CREATE_TABLE_SUBTITLE = '''CREATE TABLE IF NOT EXISTS subtitle (
          id TEXT PRIMARY KEY UNIQUE NOT NULL,
          name TEXT
        )'''

CREATE_TABLE_SCRIPT = '''CREATE TABLE IF NOT EXISTS scripts (
          id INTEGER PRIMARY KEY  AUTOINCREMENT,
          bangumi_name TEXT UNIQUE NOT NULL,
          episode INTEGER DEFAULT 0,
          status INTEGER DEFAULT 1,
          updated_time INTEGER DEFAULT 0
        )'''

CLEAR_TABLE_ = 'DELETE  FROM {}'


def init_db():
    try:
        # bangumi.db
        conn = sqlite3.connect(DB_PATH)
        conn.execute(CREATE_TABLE_BANGUMI)
        conn.execute(CREATE_TABLE_FOLLOWED)
        conn.execute(CREATE_TABLE_DOWNLOAD)
        conn.execute(CREATE_TABLE_FOLLOWED_FILTER)
        conn.execute(CREATE_TABLE_SUBTITLE)
        conn.commit()
        conn.close()

        # script.db
        conn = sqlite3.connect(SCRIPT_DB_PATH)
        conn.execute(CREATE_TABLE_SCRIPT)
        conn.commit()
        conn.close()
    except sqlite3.OperationalError:
        print_error('Open database file failed, path %s is not writable.' % BGMI_PATH)
