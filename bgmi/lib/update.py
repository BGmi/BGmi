import glob
import json
import os
import time

import requests

from bgmi import __version__, config
from bgmi.config import BGMI_PATH, PACKAGE_JSON_URL, write_default_config
from bgmi.lib import constants, db_models
from bgmi.lib.constants import SECOND_OF_WEEK
from bgmi.lib.db_models import db, get_kv_storage
from bgmi.logger import logger
from bgmi.setup import get_web_admin, install_crontab
from bgmi.sql import init_db
from bgmi.utils import (
    COLOR_END, GREEN, exec_command, print_error, print_info, print_success, print_warning
)

OLD = os.path.join(BGMI_PATH, 'old')


def _parse_semver_version(version_string):
    return [int(x) for x in version_string.split('.')]


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


def update(mark=True):
    try:
        print_info('Checking update ...')
        version = requests.get('https://pypi.python.org/pypi/bgmi/json').json()['info']['version']
        db_models.get_kv_storage()[constants.kv.LATEST_VERSION] = version

        if version > __version__:
            print_warning(
                'Please update bgmi to the latest version {}{}{}.'
                '\nThen execute `bgmi upgrade` to migrate database'.format(
                    GREEN, version, COLOR_END
                )
            )
        else:
            print_success('Your BGmi is the latest version.')

        package_json = requests.get(PACKAGE_JSON_URL).json()
        admin_version = package_json['version']
        if glob.glob(os.path.join(config.FRONT_STATIC_PATH, 'package.json')):
            with open(os.path.join(config.FRONT_STATIC_PATH, 'package.json'), 'r') as f:
                local_version = json.loads(f.read())['version']
            if _parse_semver_version(admin_version) > _parse_semver_version(local_version):
                get_web_admin()
        else:
            print_info("Use 'bgmi install' to install BGmi frontend / download delegate")
        if not mark:
            update()
            raise SystemExit
    except (requests.ConnectionError, requests.ConnectTimeout) as e:
        print_warning('Error occurs when checking update, {}'.format(str(e)))


def check_update(mark=True):
    logger.debug(f'check update {time.time()}')
    date = db_models.get_kv_storage().get(constants.kv.LAST_CHECK_UPDATE_TIME, 0)
    if time.time() - date > SECOND_OF_WEEK:
        update(mark)
        db_models.get_kv_storage()[constants.kv.LAST_CHECK_UPDATE_TIME] = int(time.time())
