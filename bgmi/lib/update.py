import os

from playhouse import db_url

from bgmi import __version__, config
from bgmi.config import BGMI_PATH, DB_URL, write_default_config
from bgmi.lib import constants
from bgmi.lib.models import db, get_kv_storage
from bgmi.setup import install_crontab
from bgmi.sql import init_db
from bgmi.utils import exec_command, print_error, print_info, print_warning

OLD = os.path.join(BGMI_PATH, 'old')


def exec_sql(sql, connect_url=DB_URL):
    try:
        print_info('connecting to {}'.format(connect_url))
        conn = db_url.connect(connect_url)
        print_info('Execute {}'.format(sql))
        conn.execute(sql)
        conn.commit()
        conn.close()
    except Exception as e:  # pragma: no cover
        print_error('Execute SQL statement failed, {}'.format(e), exit_=False)


def upgrade_version():
    if not os.path.exists(OLD):
        v = '0'
    else:
        with open(OLD, 'r+') as f:
            v = f.read()

    if v < '3.0.0':
        print_warning(
            "can't simply upgrade from bgmi<3.0.0, database structure changed too much,\n"
            "so bgmi must clear your database. type 'y' to continue"
        )
        c = input()
        if c.lower().startswith('y'):
            db.close()
            os.remove(os.path.join(BGMI_PATH, 'bangumi.db'))
            if config.IS_WINDOWS:
                remove_old_windows_cron()
            install_crontab()
            init_db()
            write_default_config()
        else:
            exit()

    get_kv_storage()[constants.kv.OLD_VERSION] = __version__


def remove_old_windows_cron():
    result = exec_command('schtasks /Delete /TN "bgmi updater" /F')
    if result:
        print_error(
            "can't delete schedule task named 'bgmi updater', please delete it manually",
            exit_=False
        )
