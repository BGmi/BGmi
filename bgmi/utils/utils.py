# coding=utf-8
from __future__ import print_function, unicode_literals
import platform
import functools
from bgmi import __version__
from bgmi.config import FETCH_URL
from bgmi.utils.langconv import Converter


GREEN = '\033[1;32m'
YELLOW = '\033[33m'
RED = '\033[1;31m'
COLOR_END = '\033[0m'

color_map = {
    'print_info': '',
    'print_success': GREEN,
    'print_warning': YELLOW,
    'print_error': RED,
}


def colorize(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if platform.system() == 'Windows':
            b, e = '', ''
        else:
            b, e = color_map.get(f.func_name, ''), COLOR_END if color_map.get(f.func_name) else ''
        args = tuple(map(lambda s: b + s + e, args))
        return f(*args, **kwargs)
    return wrapper


def _(data):
    return Converter('zh-hans').convert(data)


@colorize
def print_info(message, indicator=True):
    print('{0}{1}'.format('[*] ' if indicator else '', message))


@colorize
def print_success(message, indicator=True):
    print('{0}{1}'.format('[+] ' if indicator else '', message))


@colorize
def print_warning(message, indicator=True):
    print('{0}{1}'.format('[-] ' if indicator else '', message))


@colorize
def print_error(message, exit_=True, indicator=True):
    print('{0}{1}'.format('[x] ' if indicator else '', message))
    if exit_:
        exit(1)


def print_version():
    print('''BGmi \033[1;33mver. %s\033[0m built by \033[1;33mRicterZ\033[0m with ❤️

Github: https://github.com/RicterZ/BGmi
Email: ricterzheng@gmail.com
Blog: https://ricterz.me''' % __version__)


def test_connection():
    import requests

    try:
        requests.head(FETCH_URL, timeout=5)
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
        return data


def bug_report():
    print_error('It seems that no bangumi found, if http://dmhy.ricterz.me can \n'
                '    be opened normally, please report bug to ricterzheng@gmail.com\n'
                '    or submit issue at: https://github.com/RicterZ/BGmi/issues',
                exit_=True)


def get_terminal_col():
    import fcntl
    import termios
    import struct
    _, col, _, _ = struct.unpack(str('HHHH'), fcntl.ioctl(0, termios.TIOCGWINSZ,
                                                          struct.pack(str('HHHH'), 0, 0, 0, 0)))

    return col


if __name__ == '__main__':
    print(_('西農YUI'))
