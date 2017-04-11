# coding=utf-8
from __future__ import print_function, unicode_literals
import os
import time
import platform
import struct
import functools
import requests
from bgmi import __version__
from bgmi.config import FETCH_URL, IS_PYTHON3, BGMI_PATH

requests.packages.urllib3.disable_warnings()

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
            args = (indicator_map.get(func_name, '') + args[0], )
        return f(*args, **kwargs)
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
        requests.head(FETCH_URL, timeout=10)
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
        except:
            return 80


def check_update(mark=True):
    def update():
        print_info('Checking update ...')
        version = requests.get('https://pypi.python.org/pypi/bgmi/json', verify=False).json()['info']['version']
        if version > __version__:
            print_warning('Please update bgmi to the latest version {}{}{}.'
                          '\nThen execute `bgmi upgrade` to migrate database'.format(GREEN, version, COLOR_END))
        else:
            print_success('Your BGmi is the latest version.')
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

