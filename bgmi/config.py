# coding=utf-8
from __future__ import unicode_literals
import os
import sys
import platform

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


__all__ = ('DMHY_URL', 'BGMI_PATH', 'DB_PATH', 'BGMI_SAVE_PATH',
           'BGMI_LX_PATH', 'DOWNLOAD_DELEGATE', 'CONFIG_FILE_PATH',
           'DETAIL_URL', 'FETCH_URL', 'IS_PYTHON3', 'MAX_PAGE',
           'BGMI_TMP_PATH', 'ARIA2_PATH', 'ARIA2_RPC_URL',
           'DANMAKU_API_URL', 'COVER_URL', )

__readonly__ = ('BGMI_PATH', 'DB_PATH', 'CONFIG_FILE_PATH',
                'IS_PYTHON3', 'DETAIL_URL', 'FETCH_URL')

__writeable__ = tuple([i for i in __all__ if i not in __readonly__])


# --------- Immutable ---------- #
if platform.system() == 'Windows':
    BGMI_PATH = os.path.join(os.environ.get('USERPROFILE', None), '.bgmi')
    if not BGMI_PATH:
        raise SystemExit
else:
    BGMI_PATH = os.path.join(os.environ.get('HOME', '/tmp'), '.bgmi')

DB_PATH = os.path.join(BGMI_PATH, 'bangumi.db')
CONFIG_FILE_PATH = os.path.join(BGMI_PATH, 'bgmi.cfg')


def read_config():
    c = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE_PATH):
        write_default_config()
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

    try:
        c.write(open(CONFIG_FILE_PATH, 'w'))
    except IOError:
        print('[-] Error writing to config file and ignored')


def write_config(config=None, value=None):
    c = configparser.ConfigParser()
    c.read(CONFIG_FILE_PATH)

    if not c.has_section('bgmi'):
        c.add_section('bgmi')

    if config is not None and config not in __writeable__:
        print('{0} does not exist or not writeable'.format(config))
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


# --------- Writeable ---------- #
# Setting dmhy url
DMHY_URL = 'http://dmhy.ricterz.me'

# BGmi user path
BGMI_SAVE_PATH = os.path.join(BGMI_PATH, 'bangumi')

# Xunlei offline download
BGMI_LX_PATH = os.path.join(BGMI_PATH, 'bgmi-lx')

# aria2
ARIA2_PATH = '/usr/bin/aria2c'
ARIA2_RPC_URL = 'http://localhost:6800/rpc'

# temp path
BGMI_TMP_PATH = os.path.join(BGMI_PATH, 'tmp')

# Download delegate
DOWNLOAD_DELEGATE = 'xunlei'

# max page number of fetch bangumi info
MAX_PAGE = '2'

# danmaku api url, https://github.com/DIYgod/DPlayer#related-projects
DANMAKU_API_URL = ''

# bangumi cover url
COVER_URL = 'http://bangumi.ricterz.me/images/'


# ------------------------------ #
# !!! Read config from file and write to globals() !!!
read_config()
# ------------------------------ #


# --------- Read-Only ---------- #
# Python version
IS_PYTHON3 = sys.version_info > (3, 0)

# Detail URL
if os.environ.get('TRAVIS_CI', None):
    FETCH_URL = 'http://bangumi.ricterz.me/calendars/2016-3.html'  # for test
else:
    FETCH_URL = '{0}/cms/page/name/programme.html'.format(DMHY_URL)

DETAIL_URL = '{0}/topics/list/page/[PAGE]?keyword='.format(DMHY_URL)
