# coding=utf-8
from __future__ import print_function, unicode_literals

import functools
import gzip
import json
import os
import platform
import re
import struct
import sys
import tarfile
import time
from io import BytesIO
from shutil import rmtree, move

import requests
import urllib3

from bgmi import __version__
from bgmi.config import IS_PYTHON3, BGMI_PATH, DATA_SOURCE, BGMI_ADMIN_PATH
from bgmi.constants import SUPPORT_WEBSITE

urllib3.disable_warnings()

if platform.system() == 'Windows':
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


def indicator(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if kwargs.get('indicator', True):
            if IS_PYTHON3:
                func_name = f.__qualname__
            else:
                func_name = f.func_name
            args = (indicator_map.get(func_name, '') + args[0],)
        f(*args, **kwargs)
        sys.stdout.flush()

    return wrapper


def colorize(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if IS_PYTHON3:
            func_name = f.__qualname__
        else:
            func_name = f.func_name
        b, e = color_map.get(func_name, ''), COLOR_END if color_map.get(func_name) else ''
        args = tuple(map(lambda s: b + s + e, args))
        return f(*args, **kwargs)

    return wrapper


@indicator
@colorize
def print_info(message, indicator=True):
    print(message)


@indicator
@colorize
def print_success(message, indicator=True):
    print(message)


@indicator
@colorize
def print_warning(message, indicator=True):
    print(message)


@indicator
@colorize
def print_error(message, exit_=True, indicator=True):
    print(message)
    if exit_:
        exit(1)


def print_version():
    return '''BGmi %sver. %s%s built by %sRicterZ%s with ❤️

Github: https://github.com/RicterZ/BGmi
Email: ricterzheng@gmail.com
Blog: https://ricterz.me''' % (YELLOW, __version__, COLOR_END, YELLOW, COLOR_END)


def test_connection():
    try:
        for website in SUPPORT_WEBSITE:
            if DATA_SOURCE == website['id']:
                requests.head(website['url'], timeout=10)
    except:
        return False

    return True


def unicodeize(data):
    import bgmi.config

    if bgmi.config.IS_PYTHON3:
        if isinstance(data, bytes):
            return data.decode('utf-8')
        else:
            return data
            # return bytes(str(data), 'latin-1').decode('utf-8')
    try:
        return unicode(data.decode('utf-8'))
    except (UnicodeEncodeError, UnicodeDecodeError):
        return unicode(data.decode('gbk'))
    except (UnicodeEncodeError, UnicodeDecodeError):
        return data


def bug_report():
    print_error('It seems that no bangumi found, if https://bangumi.moe can \n'
                '    be opened normally, please report bug to ricterzheng@gmail.com\n'
                '    or submit issue at: https://github.com/RicterZ/BGmi/issues',
                exit_=True)


def get_terminal_col():
    # https://gist.github.com/jtriley/1108174
    if not platform.system() == 'Windows':
        import fcntl
        import termios

        _, col, _, _ = struct.unpack(str('HHHH'), fcntl.ioctl(0, termios.TIOCGWINSZ,
                                                              struct.pack(str('HHHH'), 0, 0, 0, 0)))

        return col
    else:
        try:
            from ctypes import windll, create_string_buffer

            # stdin handle is -10
            # stdout handle is -11
            # stderr handle is -12
            h = windll.kernel32.GetStdHandle(-12)
            csbi = create_string_buffer(22)
            res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
            if res:
                (bufx, bufy, curx, cury, wattr,
                 left, top, right, bottom,
                 maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
                sizex = right - left + 1
                # sizey = bottom - top + 1
                return sizex
            else:
                import subprocess

                cols = int(subprocess.check_output('tput cols'))
                return cols
        except:
            return 80


npm_version = '1.1.x'
package_json_url = 'https://unpkg.com/bgmi-admin@{}/package.json'.format(npm_version)
tar_url = 'https://unpkg.com/bgmi-admin@{version}/dist.tar.gz'.format(version=npm_version)


def check_update(mark=True):
    def update():
        print_info('Checking update ...')
        version = requests.get('https://pypi.python.org/pypi/bgmi/json', verify=False).json()['info']['version']
        if version > __version__:
            print_warning('Please update bgmi to the latest version {}{}{}.'
                          '\nThen execute `bgmi upgrade` to migrate database'.format(GREEN, version, COLOR_END))
        else:
            print_success('Your BGmi is the latest version.')
        admin_version = requests.get(package_json_url).json()[
            'version']

        with open(os.path.join(BGMI_ADMIN_PATH, 'package.json'), 'r') as f:
            local_version = json.loads(f.read())['version']
        if admin_version > local_version:
            get_web_admin(method='update')

    admin_version = requests.get('https://unpkg.com/bgmi-admin@1.0.x/package.json').json()['version']
    with open(os.path.join(BGMI_ADMIN_PATH, 'package.json'), 'r') as f:
        local_version = json.loads(f.read())['version']
    if admin_version > local_version:
        get_web_admin(method='update')
    if not mark:
        update()
        raise SystemExit

    version_file = os.path.join(BGMI_PATH, 'version')
    if not os.path.exists(version_file):
        with open(version_file, 'w') as f:
            f.write(str(int(time.time())))
        return update()

    with open(version_file, 'r') as f:
        try:
            data = int(f.read())
            if time.time() - 7 * 24 * 3600 > data:
                with open(version_file, 'w') as f:
                    f.write(str(int(time.time())))
                return update()
        except ValueError:
            pass


FETCH_EPISODE_ZH = re.compile("第?\s?(\d{1,3})\s?[話话集]")
FETCH_EPISODE_WITH_BRACKETS = re.compile('[【\[](\d+)\s?(?:END)?[】\]]')
FETCH_EPISODE_ONLY_NUM = re.compile('^([\d]{2,})$')
FETCH_EPISODE_RANGE = re.compile('[\d]{2,}\s?-\s?([\d]{2,})')
FETCH_EPISODE_OVA_OAD = re.compile('([\d]{2,})\s?\((?:OVA|OAD)\)]')
FETCH_EPISODE_WITH_VERSION = re.compile('[【\[](\d+)\s? *v\d(?:END)?[】\]]')
FETCH_EPISODE = (
    FETCH_EPISODE_ZH, FETCH_EPISODE_WITH_BRACKETS, FETCH_EPISODE_ONLY_NUM,
    FETCH_EPISODE_RANGE,
    FETCH_EPISODE_OVA_OAD, FETCH_EPISODE_WITH_VERSION)


def parse_episode(episode_title):
    """
    parse episode from title

    :param episode_title: episode title
    :type episode_title: str
    :return: episode of this title
    :rtype: int
    """

    _ = FETCH_EPISODE_ZH.findall(episode_title)
    if _ and _[0].isdigit():
        return int(_[0])

    _ = FETCH_EPISODE_WITH_BRACKETS.findall(episode_title)
    if _ and _[0].isdigit():
        return int(_[0])

    _ = FETCH_EPISODE_WITH_VERSION.findall(episode_title)
    if _ and _[0].isdigit():
        return int(_[0])

    for split_token in ['【', '[', ' ']:
        for i in episode_title.split(split_token):
            for regexp in FETCH_EPISODE:
                match = regexp.findall(i)
                if match and match[0].isdigit():
                    return int(match[0])
    return 0


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
    print_info('{} web admin'.format(method[0].upper() + method[1:]))
    if method == 'update':
        rmtree(BGMI_ADMIN_PATH)
        os.makedirs(BGMI_ADMIN_PATH)
    try:
        if os.environ.get('DEV', False):
            version = requests.get('http://localhost:8092/https/unpkg.com/bgmi-admin@{version}/package.json'.format(
                version=npm_version)).text
            r = requests.get(
                'http://localhost:8092/https/unpkg.com/bgmi-admin@{version}/dist.tar.gz'.format(version=npm_version))
        else:
            version = requests.get(package_json_url).text
            r = requests.get(tar_url)
    except requests.exceptions.ConnectionError:
        print_warning('failed to download web admin')
        return
    admin_zip = BytesIO(r.content)
    with gzip.GzipFile(fileobj=admin_zip) as f:
        tar_file = BytesIO(f.read())

    with tarfile.open(fileobj=tar_file) as tar_file_obj:
        tar_file_obj.extractall(path=BGMI_ADMIN_PATH)

    for file in os.listdir(os.path.join(BGMI_ADMIN_PATH, 'dist')):
        move(os.path.join(BGMI_ADMIN_PATH, 'dist', file),
             os.path.join(BGMI_ADMIN_PATH, file))
    os.removedirs(os.path.join(BGMI_ADMIN_PATH, 'dist'))
    with open(os.path.join(BGMI_ADMIN_PATH, 'package.json'), 'w+') as f:
        f.write(version)
    print_success('Web admin page {} successfully. version: {}'.format(method, json.loads(version)['version']))
