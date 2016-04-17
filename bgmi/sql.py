# coding=utf-8

CREATE_TABLE_BANGUMI = '''CREATE TABLE bangumi (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE,
          subtitle_group TEXT NOT NULL,
          keyword TEXT,
          update_time DATE NOT NULL,
          status VARCHAR(20) NOT NULL DEFAULT 0
        )'''


CREATE_TABLE_FOLLOWED = '''CREATE TABLE followed (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          bangumi_id INTEGER NOT NULL,
          episode INTEGER DEFAULT 0
        )'''


INSERT_TEST_DATA = '''INSERT INTO bangumi (
  name, subtitle_group, update_time, status, keyword
  ) VALUES ("test", "rr", "Sun", 0, "test")'''