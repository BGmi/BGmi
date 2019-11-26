import glob
import gzip
import json
import os
import signal
import struct
import subprocess
import tarfile
import time
from io import BytesIO
from shutil import move, rmtree

import requests

from bgmi import __admin_version__, __version__, config
from bgmi.lib import constants, db_models
from bgmi.logger import logger
from bgmi.pure_utils import normalize_path, parallel

from ._decorator import COLOR_END, GREEN, _indicator, colorize, disable_in_test, log_utils_function

SECOND_OF_WEEK = 7 * 24 * 3600

if os.environ.get('TRAVIS_CI', False):
    NPM_REGISTER_DOMAIN = 'registry.npmjs.com'
else:
    NPM_REGISTER_DOMAIN = 'registry.npm.taobao.org'
FRONTEND_NPM_URL = f'https://{NPM_REGISTER_DOMAIN}/bgmi-frontend/'
PACKAGE_JSON_URL = f'https://{NPM_REGISTER_DOMAIN}/bgmi-frontend/{__admin_version__}'


@disable_in_test
@_indicator
@colorize
def print_info(message, indicator=True):
    logger.info(message)


@disable_in_test
@_indicator
@colorize
def print_success(message, indicator=True):
    logger.info(message)


@disable_in_test
@_indicator
@colorize
def print_warning(message, indicator=True):
    logger.warning(message)


@disable_in_test
@_indicator
@colorize
def print_error(message, exit_: bool = True, indicator=True):
    logger.error(message)

    if exit_:
        exit(1)


def bug_report():  # pragma: no cover
    print_error(
        'It seems that no bangumi found, if https://bangumi.moe can \n'
        '    be opened normally, '
        'please submit issue at: https://github.com/BGmi/BGmi/issues',
        exit_=True
    )


@log_utils_function
def get_terminal_col():  # pragma: no cover
    # https://gist.github.com/jtriley/1108174
    if not config.IS_WINDOWS:
        import fcntl
        import termios

        _, col, _, _ = struct.unpack(
            'HHHH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0))
        )

        return col
    try:
        from ctypes import windll, create_string_buffer

        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12
        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (_, _, _, _, _, left, _, right, _, _, _) = struct.unpack('hhhhHhhhhhh', csbi.raw)
            sizex = right - left + 1
            # sizey = bottom - top + 1
            return sizex
        cols = int(subprocess.check_output('tput cols'))
        return cols
    except BaseException:
        return 80


def _parse_version(version_string):
    return [int(x) for x in version_string.split('.')]


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
            if _parse_version(admin_version) > _parse_version(local_version):
                get_web_admin()
        else:
            print_info("Use 'bgmi install' to install BGmi frontend / download delegate")
        if not mark:
            update()
            raise SystemExit
    except (requests.ConnectionError, requests.ConnectTimeout) as e:
        print_warning('Error occurs when checking update, {}'.format(str(e)))


@log_utils_function
def check_update(mark=True):
    date = db_models.get_kv_storage().get(constants.kv.LAST_CHECK_UPDATE_TIME, 0)
    if time.time() - date > SECOND_OF_WEEK:
        update(mark)
        db_models.get_kv_storage()[constants.kv.LAST_CHECK_UPDATE_TIME] = int(time.time())


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
        unzip_zipped_file(r.content, version)
        print_success('Web admin page install successfully. version: {}'.format(version['version']))
    except requests.exceptions.ConnectionError:
        print_error('failed to download web admin')
    except json.JSONDecodeError:
        print_error('failed to download web admin')


def unzip_zipped_file(file_content, front_version):
    admin_zip = BytesIO(file_content)
    with gzip.GzipFile(fileobj=admin_zip) as f:
        tar_file = BytesIO(f.read())

    rmtree(config.FRONT_STATIC_PATH)
    os.makedirs(config.FRONT_STATIC_PATH)

    with tarfile.open(fileobj=tar_file) as tar_file_obj:
        tar_file_obj.extractall(path=config.FRONT_STATIC_PATH)

    for file in os.listdir(os.path.join(config.FRONT_STATIC_PATH, 'package', 'dist')):
        move(
            os.path.join(config.FRONT_STATIC_PATH, 'package', 'dist', file),
            os.path.join(config.FRONT_STATIC_PATH, file)
        )
    with open(os.path.join(config.FRONT_STATIC_PATH, 'package.json'), 'w+') as f:
        f.write(json.dumps(front_version))


@log_utils_function
def convert_cover_url_to_path(cover_url):
    """
    convert bangumi cover to file path

    :param cover_url: bangumi cover path
    :type cover_url:str
    :rtype: (str,str)
    :return: dir_path, file_path
    """

    cover_url = normalize_path(cover_url)
    file_path = os.path.join(config.SAVE_PATH, 'cover')
    file_path = os.path.join(file_path, cover_url)
    dir_path = os.path.dirname(file_path)

    return dir_path, file_path


@log_utils_function
def download_file(url):
    if url.startswith('https://') or url.startswith('http://'):
        print_info(f'Download: {url}')
        r = requests.get(url)

        _, file_path = convert_cover_url_to_path(url)

        with open(file_path, 'wb') as f:
            f.write(r.content)


@log_utils_function
def download_cover(cover_url_list):
    """

    :param cover_url_list:
    :type cover_url_list: list
    :return:
    """
    for url in cover_url_list:
        dir_path, _ = convert_cover_url_to_path(url)

        if os.path.exists(dir_path):
            if not os.path.isdir(dir_path):
                os.remove(dir_path)

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    parallel(download_file, cover_url_list)


# global Ctrl-C signal handler
def signal_handler(signal, frame):  # pragma: no cover # pylint: disable=W0613

    print_error('User aborted, quit')


signal.signal(signal.SIGINT, signal_handler)
