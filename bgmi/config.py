# coding=utf-8
from __future__ import unicode_literals
import os
import sys

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


__all__ = ('DMHY_URL', 'BGMI_PATH', 'DB_PATH', 'BGMI_SAVE_PATH',
           'BGMI_LX_PATH', 'DOWNLOAD_DELEGATE', 'CONFIG_FILE_PATH',
           'DETAIL_URL', 'FETCH_URL', 'IS_PYTHON3', 'MAX_PAGE')

__readonly__ = ('BGMI_PATH', 'DB_PATH', 'CONFIG_FILE_PATH',
                'IS_PYTHON3', 'DETAIL_URL', 'FETCH_URL')

__writeable__ = tuple([i for i in __all__ if i not in __readonly__])


# --------- Immutable ---------- #
BGMI_PATH = os.path.join(os.environ.get('HOME', '/tmp'), '.bgmi')
DB_PATH = os.path.join(BGMI_PATH, 'bangumi.db')
CONFIG_FILE_PATH = os.path.join(BGMI_PATH, 'bgmi.cfg')


def read_config():
    c = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE_PATH):
        return
    c.read(CONFIG_FILE_PATH)

    for i in __writeable__:
        if c.has_option('bgmi', i):
            globals().update({i: c.get('bgmi', i)})


def print_config():
    c = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE_PATH):
        return
    c.read(CONFIG_FILE_PATH)
    for i in __writeable__:
        print('{0}={1}'.format(i, c.get('bgmi', i)))


def write_default_config():
    c = configparser.ConfigParser()
    if not c.has_section('bgmi'):
        c.add_section('bgmi')

    for i in __writeable__:
        v = globals().get(i, None)
        c.set('bgmi', i, v)

    c.write(open(CONFIG_FILE_PATH, 'w'))


def write_config(config=None, value=None):
    c = configparser.ConfigParser()
    c.read(CONFIG_FILE_PATH)

    if not c.has_section('bgmi'):
        c.add_section('bgmi')

    if config is not None and config not in __writeable__:
        print('{0} is not exist or not writeable'.format(config))
        exit(1)

    for i in __writeable__:
        v = globals().get(i, None)
        c.set('bgmi', i, v)

    try:
        if config is None and value is None:
            print_config()
            return
        elif value is None:
            print('{0}={1}'.format(config, c.get('bgmi', config)))
            return
        else:
            if config in __writeable__:
                c.set('bgmi', config, value)
                with open(CONFIG_FILE_PATH, 'w') as f:
                    c.write(f)
            print_config()

    except (configparser.NoOptionError):
        write_default_config()



def _refresh_config():
    pass
# --------- Writeable ---------- #
# Setting dmhy url
DMHY_URL = 'http://dmhy.ricterz.me'

# BGmi user path
BGMI_SAVE_PATH = os.path.join(BGMI_PATH, 'bangumi')

# Xunlei offline download
BGMI_LX_PATH = os.path.join(BGMI_PATH, 'bgmi-lx')

# Download delegate
DOWNLOAD_DELEGATE = 'xunlei'

# max page number of fetch bangumi info
MAX_PAGE = '2'


# ------------------------------ #
# !!! Read config from file and write to globals() !!!
read_config()
# ------------------------------ #


# --------- Read-Only ---------- #
# Python version
IS_PYTHON3 = sys.version_info > (3, 0)

# Detail URL
FETCH_URL = '{0}/cms/page/name/programme.html'.format(DMHY_URL)
DETAIL_URL = '{0}/topics/list/page/[PAGE]?keyword='.format(DMHY_URL)


if __name__ == '__main__':
    for i in __all__:
        print(i, globals().get(i, None))
