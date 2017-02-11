# coding=utf-8
import os
import sys
import sqlite3

from bgmi import __version__
from bgmi.config import DB_PATH, BGMI_PATH
from bgmi.utils.utils import print_error, print_info

OLD = os.path.join(BGMI_PATH, 'old')


def exec_sql(sql):
    try:
        print_info('Execute {}'.format(sql))
        conn = sqlite3.connect(DB_PATH)
        conn.execute(sql)
        conn.commit()
        conn.close()
    except sqlite3.OperationalError:
        print_error('Execute SQL statement failed', exit_=False)


def update_database():
    if not os.path.exists(OLD):
        v = '0'
        with open(OLD, 'w') as f:
            f.write(__version__)
    else:
        with open(OLD, 'r+b') as f:
            v = f.read()
            f.seek(0)
            f.write(__version__)

    if v < '1.0.25':
        exec_sql('ALTER TABLE filter ADD COLUMN regex')
