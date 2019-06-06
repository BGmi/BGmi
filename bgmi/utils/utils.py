import glob
import gzip
import inspect
import json
import os
import signal
import struct
import subprocess
import tarfile
import time
from io import BytesIO
from multiprocessing.pool import ThreadPool
from pathlib import Path
from shutil import move, rmtree
from typing import TextIO, Union

import requests
from tornado import template

from bgmi import __admin_version__, __version__, config
from bgmi.lib import constants
from bgmi.lib.db_models import get_kv_storage
from bgmi.logger import logger

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
def print_error(message, exit_=True, indicator=True):
    logger.error(message)

    if exit_:
        exit(1)


@log_utils_function
def test_connection():
    try:
        requests.request('head', 'https://api.bgm.tv/calendar', timeout=3)
    except BaseException:
        return False
    return True


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
        get_kv_storage()[constants.kv.LATEST_VERSION] = version
        # with open(os.path.join(BGMI_PATH, 'latest'), 'w') as f:
        #     f.write(version)

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
    except Exception as e:
        if os.environ.get('DEBUG'):
            raise e
        print_warning('Error occurs when checking update, {}'.format(str(e)))


@log_utils_function
def check_update(mark=True):
    date = get_kv_storage().get(constants.kv.LAST_CHECK_UPDATE_TIME, '0')
    if time.time() - int(date) > SECOND_OF_WEEK:
        update(mark)
        get_kv_storage()[constants.kv.LAST_CHECK_UPDATE_TIME] = str(int(time.time()))


@log_utils_function
def normalize_path(url):
    """
    normalize link to path

    :param url: path or url to normalize
    :type url: str
    :return: normalized path
    :rtype: str
    """
    url = url.replace('http://', 'http/').replace('https://', 'https/')
    illegal_char = [':', '*', '?', '"', '<', '>', '|', "'"]
    for char in illegal_char:
        url = url.replace(char, '')

    if url.startswith('/'):
        return url[1:]
    return url


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


def full_to_half(s):
    n = []
    # s = s.decode('utf-8')
    for char in s:
        num = ord(char)
        if num == 0x3000:
            num = 32
        elif 0xFF01 <= num <= 0xFF5E:
            num -= 0xfee0
        num = chr(num)
        n.append(num)
    return ''.join(n)


@log_utils_function
def exec_command(command: str) -> int:
    """
    exec command and stdout iconv
    :return: command exec result
    """
    status, stdout = subprocess.getstatusoutput(command)
    print(stdout)
    return status


def render_template(path_or_file: Union[str, Path, TextIO], ctx: dict = None, **kwargs):
    """
    read file content and render it as tornado template with kwargs or ctx

    :param ctx:
    :param path_or_file: path-like or file-like object
    :param kwargs:
    :rtype: str
    :return:
    """
    if ctx and kwargs:
        raise ValueError('render_template and only be called with ctx or kwargs')
    if hasattr(path_or_file, 'read'):
        # input is a file
        content = path_or_file.read()
    else:
        # py3.4 can't open pathlib.Path directly, need to be str
        with open(str(path_or_file), 'r', encoding='utf8') as f:
            content = f.read()
    template_obj = template.Template(content, autoescape='')
    return template_obj.generate(**(ctx or kwargs)).decode('utf-8')


def parallel(func, args):
    with ThreadPool(4) as pool:
        try:
            sign = inspect.signature(func)
            if len(sign.parameters) == 1:
                res = pool.starmap_async(func, ((x, ) for x in args))
            else:
                res = pool.starmap_async(func, args)
            return res.get()
        except KeyboardInterrupt:
            signal_handler(None, None)


# global Ctrl-C signal handler
def signal_handler(signal, frame):  # pragma: no cover # pylint: disable=W0613

    print_error('User aborted, quit')


signal.signal(signal.SIGINT, signal_handler)
