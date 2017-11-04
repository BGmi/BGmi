# coding=utf-8
import os
import sqlite3

from bgmi import __version__
from bgmi.config import DB_PATH, BGMI_PATH, SCRIPT_DB_PATH
from bgmi.utils import print_error, print_info

OLD = os.path.join(BGMI_PATH, 'old')


def exec_sql(sql, db=DB_PATH):
    try:
        print_info('Execute {}'.format(sql))
        conn = sqlite3.connect(db)
        conn.execute(sql)
        conn.commit()
        conn.close()
    except sqlite3.OperationalError:  # pragma: no cover
        print_error('Execute SQL statement failed', exit_=False)


def update_database():
    if not os.path.exists(OLD):
        v = '0'
        with open(OLD, 'w') as f:
            f.write(__version__)
    else:
        with open(OLD, 'r+') as f:
            v = f.read()
            f.seek(0)
            f.write(__version__)

    if v < '1.0.25':
        exec_sql('ALTER TABLE filter ADD COLUMN regex')

    if v < '1.4.1':
        exec_sql('ALTER TABLE scripts ADD COLUMN update_time INTEGER', SCRIPT_DB_PATH)

    if v < '2.0.2':
        from bgmi.fetch import website
        from bgmi.models import Bangumi
        week_list = Bangumi.get_all_bangumi()
        for kay, value in week_list.items():
            for bangumi in value:
                b = Bangumi.get(name=bangumi['name'])
                b.cover = website.cover_url + bangumi['cover']
                b.save()
