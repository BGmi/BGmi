import json
import os

import requests

from bgmi import utils
from bgmi.config import FRONTEND_NPM_URL, PACKAGE_JSON_URL, config_obj
from bgmi.utils import exec_command, print_error, print_info, print_success, print_warning


def install_crontab() -> None:
    if os.getenv('BGMI_IN_DOCKER'):
        print_warning('env BGMI_IN_DOCKER exists, skip install crontab')
        return
    print_info('Installing crontab job')
    if config_obj.IS_WINDOWS:
        base = os.path.join(os.path.dirname(__file__), 'others\\windows\\cron')
        exec_command(
            'SCHTASKS /Create /TN "bgmi calendar updater" /SC HOURLY /MO 2 '
            '/TR "{tr}" /F'.format(tr=os.path.join(base, 'cal.vbs'))
        )

        exec_command(
            'SCHTASKS /Create /TN "bgmi bangumi updater" /SC HOURLY /MO 12 '
            '/TR "{tr}" /F'.format(tr=os.path.join(base, 'update.vbs'))
        )
    else:
        path = os.path.join(os.path.dirname(__file__), 'others/crontab.sh')
        exec_command("bash '%s'" % path)


def create_dir() -> None:
    path_to_create = (
        config_obj.BGMI_PATH,
        config_obj.SAVE_PATH,
        config_obj.TMP_PATH,
        config_obj.SCRIPT_PATH,
        config_obj.TOOLS_PATH,
        config_obj.FRONT_STATIC_PATH,
    )

    # bgmi home dir
    try:
        for path in path_to_create:
            if not os.path.exists(path):
                os.makedirs(path)
                print_success('%s created successfully' % path)
    except OSError as e:
        print_error('Error: {}'.format(str(e)))


def get_web_admin():
    print_info('Fetching BGmi frontend')
    try:
        r = requests.get(FRONTEND_NPM_URL).json()
        version = requests.get(PACKAGE_JSON_URL).json()
        if 'error' in version and version['reason'] == 'document not found':  # pragma: no cover
            print_error(
                'Cnpm has not synchronized the latest version of BGmi-frontend from npm, '
                'please try it later'
            )
        tar_url = r['versions'][version['version']]['dist']['tarball']
        r = requests.get(tar_url)
        utils.unzip_zipped_file(r.content, version)
        print_success('Web admin page install successfully. version: {}'.format(version['version']))
    except requests.exceptions.ConnectionError:
        print_error('failed to download web admin')
    except json.JSONDecodeError:
        print_error('failed to download web admin')
