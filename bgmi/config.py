# coding=utf-8
from __future__ import unicode_literals
import os
import sys
import platform

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


# download delegate
__wget__ = ('WGET_PATH', )
__thunder__ = ('XUNLEI_LX_PATH', )
__aria2__ = ('ARIA2_RPC_URL', 'ARIA2_PATH', 'ARIA2_RPC_TOKEN', )
__transmission__ = ('TRANSMISSION_RPC_URL', 'TRANSMISSION_RPC_PORT')

__download_delegate__ = __wget__ + __thunder__ + __aria2__ + __transmission__

# fake __all__
__all__ = ('BANGUMI_MOE_URL', 'BGMI_PATH', 'DB_PATH', 'BGMI_SAVE_PATH',
           'DOWNLOAD_DELEGATE', 'CONFIG_FILE_PATH', 'MAX_PAGE',
           'DETAIL_URL', 'FETCH_URL', 'IS_PYTHON3',
           'BGMI_TMP_PATH', 'DANMAKU_API_URL', 'COVER_URL', 'LANG')

# cannot be rewrite
__readonly__ = ('BGMI_PATH', 'DB_PATH', 'CONFIG_FILE_PATH',
                'IS_PYTHON3', 'DETAIL_URL', 'FETCH_URL')

# writeable
__writeable__ = tuple([i for i in __all__ if i not in __readonly__])

# the real __all__
__all__ = __all__ + __download_delegate__


download_delegate_map = {
    'rr!': __wget__,
    'aria2-rpc': __aria2__,
    'xunlei': __thunder__,
    'transmission-rpc': __transmission__,
}


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

    for i in download_delegate_map.get(DOWNLOAD_DELEGATE):
        if c.has_option(DOWNLOAD_DELEGATE, i):
            globals().update({i: c.get(DOWNLOAD_DELEGATE, i)})

def print_config():
    c = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE_PATH):
        return

    c.read(CONFIG_FILE_PATH)
    print('[bgmi]')
    for i in __writeable__:
        print('{0}={1}'.format(i, c.get('bgmi', i)))

    print('\n[{0}]'.format(DOWNLOAD_DELEGATE))
    for i in download_delegate_map.get(DOWNLOAD_DELEGATE):
        print('{0}={1}'.format(i, c.get(DOWNLOAD_DELEGATE, i)))


def write_default_config():
    c = configparser.ConfigParser()
    if not c.has_section('bgmi'):
        c.add_section('bgmi')

    for i in __writeable__:
        v = globals().get(i, None)
        c.set('bgmi', i, v)

    if DOWNLOAD_DELEGATE not in download_delegate_map.keys():
        raise Exception(DOWNLOAD_DELEGATE)

    if not c.has_section(DOWNLOAD_DELEGATE):
        c.add_section(DOWNLOAD_DELEGATE)

    for i in download_delegate_map.get(DOWNLOAD_DELEGATE):
        v = globals().get(i, None)
        c.set(DOWNLOAD_DELEGATE, i, v)

    try:
        c.write(open(CONFIG_FILE_PATH, 'w'))
    except IOError:
        print('[-] Error writing to config file and ignored')


def write_config(config=None, value=None):
    if not os.path.exists(CONFIG_FILE_PATH):
        write_default_config()

    c = configparser.ConfigParser()
    c.read(CONFIG_FILE_PATH)

    if config is not None and config not in __writeable__ and config not in __download_delegate__:
        print('{0} does not exist or not writeable'.format(config))
        exit(1)

    try:
        if config is None and value is None:
            print_config()
        elif value is None:
            if config in __download_delegate__:
                print('{0}={1}'.format(config, c.get(DOWNLOAD_DELEGATE, config)))
            else:
                print('{0}={1}'.format(config, c.get('bgmi', config)))
        else:
            if config in __writeable__:
                c.set('bgmi', config, value)
                with open(CONFIG_FILE_PATH, 'w') as f:
                    c.write(f)
                read_config()

            if config == 'DOWNLOAD_DELEGATE':
                if not c.has_section(DOWNLOAD_DELEGATE):
                    c.add_section(DOWNLOAD_DELEGATE)
                    for i in download_delegate_map.get(DOWNLOAD_DELEGATE):
                        v = globals().get(i, '')
                        c.set(DOWNLOAD_DELEGATE, i, v)

                    with open(CONFIG_FILE_PATH, 'w') as f:
                        c.write(f)

            if config in download_delegate_map.get(DOWNLOAD_DELEGATE):
                c.set(DOWNLOAD_DELEGATE, config, value)
                with open(CONFIG_FILE_PATH, 'w') as f:
                    c.write(f)

            print_config()

    except configparser.NoOptionError:
        write_default_config()


# --------- Writeable ---------- #
# Setting bangumi.moe url
BANGUMI_MOE_URL = 'http://bangumi_moe.ricterz.me'

# BGmi user path
BGMI_SAVE_PATH = os.path.join(BGMI_PATH, 'bangumi')

# Xunlei offline download
XUNLEI_LX_PATH = os.path.join(BGMI_PATH, 'bgmi-lx')

# temp path
BGMI_TMP_PATH = os.path.join(BGMI_PATH, 'tmp')

# Download delegate
DOWNLOAD_DELEGATE = 'aria2-rpc'

# danmaku api url, https://github.com/DIYgod/DPlayer#related-projects
DANMAKU_API_URL = ''

# bangumi cover url
COVER_URL = 'https://bangumi_moe.ricterz.me'

# language
LANG = 'zh_cn'

# max page
MAX_PAGE = '3'

# aria2
ARIA2_PATH = '/usr/bin/aria2c'
ARIA2_RPC_URL = 'http://localhost:6800/rpc'
ARIA2_RPC_TOKEN = 'token:'

# path of wget
WGET_PATH = '/usr/bin/wget'

# transmission-rpc
TRANSMISSION_RPC_URL = '127.0.0.1'
TRANSMISSION_RPC_PORT = '9091'


# ------------------------------ #
# !!! Read config from file and write to globals() !!!
read_config()
# ------------------------------ #


# --------- Read-Only ---------- #
# Python version
IS_PYTHON3 = sys.version_info > (3, 0)

# Detail URL
__split = '/' if not BANGUMI_MOE_URL.endswith('/') else ''
FETCH_URL = '{0}{1}api/bangumi/current'.format(BANGUMI_MOE_URL, __split)
TEAM_URL = '{0}{1}api/team/working'.format(BANGUMI_MOE_URL, __split)
NAME_URL = '{0}{1}api/tag/fetch'.format(BANGUMI_MOE_URL, __split)
DETAIL_URL = '{0}{1}api/torrent/search'.format(BANGUMI_MOE_URL, __split)
