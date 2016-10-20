# coding=utf-8

CREATE_TABLE_BANGUMI = '''CREATE TABLE IF NOT EXISTS bangumi (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE,
          subtitle_group TEXT NOT NULL,
          keyword TEXT,
          update_time CHAR(5) NOT NULL,
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
          exclude TEXT
        )'''