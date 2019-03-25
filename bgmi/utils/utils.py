# coding=utf-8
import functools
import glob
import gzip
import inspect
import json
import os
import struct
import subprocess
import sys
import tarfile
import time
from io import BytesIO
from multiprocessing.pool import ThreadPool
from shutil import rmtree, move

import requests
import urllib3

from bgmi import __version__, __admin_version__
from bgmi.config import FRONT_STATIC_PATH, SAVE_PATH
from bgmi.lib import constants
from bgmi.lib.models import get_kv_storage
from bgmi.logger import logger

SECOND_OF_WEEK = 7 * 24 * 3600


def _dict_as_called(f, args, kwargs):
    """ return a dict of all the args and kwargs as the keywords they would
    be received in a real f call.  It does not call f.
    """

    names, args_name, kwargs_name, defaults, _, _, _ = inspect.getfullargspec(f)

    # assign basic args
    params = {}
    if args_name:
        basic_arg_count = len(names)
        params.update(zip(names[:], args))  # zip stops at shorter sequence
        params[args_name] = args[basic_arg_count:]
    else:
        params.update(zip(names, args))

    # assign kwargs given
    if kwargs_name:
        params[kwargs_name] = {}
        for kw, value in kwargs.items():
            if kw in names:
                params[kw] = value
            else:
                params[kwargs_name][kw] = value
    else:
        params.update(kwargs)

    # assign defaults
    if defaults:
        for pos, value in enumerate(defaults):
            if names[-len(defaults) + pos] not in params:
                params[names[-len(defaults) + pos]] = value

    return params


def log_utils_function(func):
    @functools.wraps(func)
    def echo_func(*func_args, **func_kwargs):
        r = func(*func_args, **func_kwargs)
        called_with = _dict_as_called(func, func_args, func_kwargs)
        logger.debug("util.%s %s -> `%s`", func.__name__, called_with, r)
        return r

    return echo_func


def disable_in_test(func):
    @functools.wraps(func)
    def echo_func(*func_args, **func_kwargs):
        if os.environ.get('UNITTEST'):
            return
        r = func(*func_args, **func_kwargs)
        return r

    return echo_func


urllib3.disable_warnings()

# monkey patch for dev
if os.environ.get('DEV', False):  # pragma: no cover
    def replace_url(url):
        if url.startswith('https://'):
            url = url.replace('https://', 'http://localhost:8092/https/')
        elif url.startswith('http://'):
            url = url.replace('http://', 'http://localhost:8092/http/')
        return url


    from copy import deepcopy
    from requests import Session

    origin_request = deepcopy(Session.request)


    def req(self, method, url, **kwargs):
        if os.environ.get('BGMI_SHOW_ALL_NETWORK_REQUEST'):
            print(url)
        url = replace_url(url)
        # traceback.print_stack(limit=8)
        return origin_request(self, method, url, **kwargs)


    Session.request = req

if sys.platform.startswith('win'):  # pragma: no cover
    GREEN = ''
    YELLOW = ''
    RED = ''
    COLOR_END = ''
else:
    GREEN = '\033[1;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[1;31m'
    COLOR_END = '\033[0m'

color_map = {
    'print_info': '',
    'print_success': GREEN,
    'print_warning': YELLOW,
    'print_error': RED,
}

indicator_map = {
    'print_info': '[*] ',
    'print_success': '[+] ',
    'print_warning': '[-] ',
    'print_error': '[x] ',
}

NPM_REGISTER_DOMAIN = 'registry.npmjs.com' if os.environ.get('TRAVIS_CI', False) else 'registry.npm.taobao.org'
FRONTEND_NPM_URL = 'https://{}/bgmi-frontend/'.format(NPM_REGISTER_DOMAIN)
PACKAGE_JSON_URL = 'https://{}/bgmi-frontend/{}'.format(NPM_REGISTER_DOMAIN, __admin_version__)


def _indicator(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if kwargs.get('indicator', True):
            func_name = f.__qualname__
            args = (indicator_map.get(func_name, '') + args[0],)
        f(*args, **kwargs)
        sys.stdout.flush()

    return wrapper


def colorize(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        func_name = f.__qualname__
        b, e = color_map.get(func_name, ''), COLOR_END if color_map.get(func_name) else ''
        args = tuple(map(lambda s: b + s + e, args))
        return f(*args, **kwargs)

    return wrapper


@disable_in_test
@_indicator
@colorize
def print_info(message, indicator=True):
    logger.info(message)
    print(message)


@disable_in_test
@_indicator
@colorize
def print_success(message, indicator=True):
    logger.info(message)
    print(message)


@disable_in_test
@_indicator
@colorize
def print_warning(message, indicator=True):
    logger.warning(message)
    print(message)


@disable_in_test
@_indicator
@colorize
def print_error(message, exit_=True, indicator=True):
    logger.error(message)
    print(message)
    if exit_:
        exit(1)


def print_version():
    return '''BGmi %sver. %s%s built by %sRicterZ%s with ❤️

Github: https://github.com/BGmi/BGmi
Email: ricterzheng@gmail.com
Blog: https://ricterz.me''' % (YELLOW, __version__, COLOR_END, YELLOW, COLOR_END)


@log_utils_function
def test_connection():
    try:
        requests.request('head', 'https://api.bgm.tv/calendar', timeout=3)
    except BaseException:
        return False
    return True


def bug_report():  # pragma: no cover
    print_error('It seems that no bangumi found, if https://bangumi.moe can \n'
                '    be opened normally, please submit issue at: https://github.com/BGmi/BGmi/issues',
                exit_=True)


@log_utils_function
def get_terminal_col():  # pragma: no cover
    # https://gist.github.com/jtriley/1108174
    if not sys.platform.startswith('win'):
        import fcntl
        import termios

        _, col, _, _ = struct.unpack(str('HHHH'), fcntl.ioctl(0, termios.TIOCGWINSZ,
                                                              struct.pack(str('HHHH'), 0, 0, 0, 0)))

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
            (_, _, _, _, _, left, _, right, _, _, _) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            sizex = right - left + 1
            # sizey = bottom - top + 1
            return sizex
        import subprocess

        cols = int(subprocess.check_output('tput cols'))
        return cols
    except BaseException:
        return 80


def update(mark=True):
    try:
        print_info('Checking update ...')
        version = requests.get('https://pypi.python.org/pypi/bgmi/json').json()['info']['version']
        get_kv_storage()[constants.kv.LATEST_VERSION] = version
        # with open(os.path.join(BGMI_PATH, 'latest'), 'w') as f:
        #     f.write(version)

        if version > __version__:
            print_warning('Please update bgmi to the latest version {}{}{}.'
                          '\nThen execute `bgmi upgrade` to migrate database'
                          .format(GREEN, version, COLOR_END))
        else:
            print_success('Your BGmi is the latest version.')

        package_json = requests.get(PACKAGE_JSON_URL).json()
        admin_version = package_json['version']
        if glob.glob(os.path.join(FRONT_STATIC_PATH, 'package.json')):
            with open(os.path.join(FRONT_STATIC_PATH, 'package.json'), 'r') as f:
                local_version = json.loads(f.read())['version']
            if [int(x) for x in admin_version.split('.')] > [int(x) for x in local_version.split('.')]:
                get_web_admin(method='update')
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
    data = get_kv_storage().get(constants.kv.LAST_CHECK_UPDATE_TIME, 0)
    if time.time() - data > SECOND_OF_WEEK:
        get_kv_storage()[constants.kv.LAST_CHECK_UPDATE_TIME] = int(time.time())
        return update(mark)


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
    else:
        return url


def get_web_admin(method):
    print_info('{}ing BGmi frontend'.format(method.title()))
    try:
        r = requests.get(FRONTEND_NPM_URL).json()
        version = requests.get(PACKAGE_JSON_URL).json()
        if 'error' in version and version['reason'] == "document not found":  # pragma: no cover
            print_error("Cnpm has not synchronized the latest version of BGmi-frontend from npm, "
                        "please try it later")
            return
        tar_url = r['versions'][version['version']]['dist']['tarball']
        r = requests.get(tar_url)
    except requests.exceptions.ConnectionError:
        print_warning('failed to download web admin')
        return
    except json.JSONDecodeError:
        print_warning('failed to download web admin')
        return
    unzip_zipped_file(r.content, version)
    print_success('Web admin page {} successfully. version: {}'.format(method, version['version']))


def unzip_zipped_file(file_content, front_version):
    admin_zip = BytesIO(file_content)
    with gzip.GzipFile(fileobj=admin_zip) as f:
        tar_file = BytesIO(f.read())

    rmtree(FRONT_STATIC_PATH)
    os.makedirs(FRONT_STATIC_PATH)

    with tarfile.open(fileobj=tar_file) as tar_file_obj:
        tar_file_obj.extractall(path=FRONT_STATIC_PATH)

    for file in os.listdir(os.path.join(FRONT_STATIC_PATH, 'package', 'dist')):
        move(os.path.join(FRONT_STATIC_PATH, 'package', 'dist', file),
             os.path.join(FRONT_STATIC_PATH, file))
    with open(os.path.join(FRONT_STATIC_PATH, 'package.json'), 'w+') as f:
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
    file_path = os.path.join(SAVE_PATH, 'cover')
    file_path = os.path.join(file_path, cover_url)
    dir_path = os.path.dirname(file_path)

    return dir_path, file_path


@log_utils_function
def download_file(url):
    if url.startswith('https://') or url.startswith('http://'):
        print_info('Download: {}'.format(url))
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
        dir_path, file_path = convert_cover_url_to_path(url)

        if os.path.exists(dir_path):
            if not os.path.isdir(dir_path):
                os.remove(dir_path)

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    p = ThreadPool(4)
    p.map(download_file, cover_url_list)
    p.close()


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
