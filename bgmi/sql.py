# coding=utf-8

CREATE_TABLE_BANGUMI = '''CREATE TABLE bangumi (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE,
          subtitle_group TEXT NOT NULL,
          keyword TEXT,
          update_time CHAR(5) NOT NULL,
          status INTEGER DEFAULT 0
        )'''


CREATE_TABLE_FOLLOWED = '''CREATE TABLE followed (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          bangumi_name TEXT NOT NULL UNIQUE,
          episode INTEGER DEFAULT 0,
          status INTEGER DEFAULT 1,
          subtitle_group TEXT,
          updated_time INTEGER DEFAULT 0
        )'''


CREATE_TABLE_DOWNLOAD = '''CREATE TABLE download (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          title TEXT NOT NULL,
          episode INTEGER DEFAULT 0,
          download TEXT,
          status INTEGER DEFAULT 0
        )'''
