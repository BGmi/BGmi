# coding=utf-8

import configparser
import hashlib
import os
import platform
import random

# download delegate
__transmission__ = (
    'TRANSMISSION_RPC_URL',
    'TRANSMISSION_RPC_PORT',
    'TRANSMISSION_RPC_USERNAME',
    'TRANSMISSION_RPC_PASSWORD',
)
__aria2__ = (
    'ARIA2_RPC_URL',
    'ARIA2_RPC_TOKEN',
)
__deluge__ = ('DELUGE_RPC_URL', 'DELUGE_RPC_PASSWORD')

__download_delegate__ = __aria2__ + __transmission__ + __deluge__

# fake __all__
__all__ = (
    'BANGUMI_MOE_URL',
    'SAVE_PATH',
    'DOWNLOAD_DELEGATE',
    'DB_URL',
    'KV_DB_PATH',
    'MAX_PAGE',
    'TMP_PATH',
    'DANMAKU_API_URL',
    'DISABLED_DATA_SOURCE',
    'LANG',
    'FRONT_STATIC_PATH',
    'ADMIN_TOKEN',
    'SHARE_DMHY_URL',
    'GLOBAL_FILTER',
    'ENABLE_GLOBAL_FILTER',
    'TORNADO_SERVE_STATIC_FILES',
)

# cannot be rewrite
__readonly__ = (
    'BGMI_PATH',
    'CONFIG_FILE_PATH',
    'TOOLS_PATH',
    'SCRIPT_PATH',
    'KV_DB_PATH',
    'FRONT_STATIC_PATH',
)

# writeable
__writeable__ = tuple([i for i in __all__ if i not in __readonly__])

# the real __all__
__all__ = __all__ + __download_delegate__ + __readonly__

DOWNLOAD_DELEGATE_MAP = {
    'aria2-rpc': __aria2__,
    'transmission-rpc': __transmission__,
    'deluge-rpc': __deluge__,
}


def get_bgmi_path():
    if not os.environ.get('BGMI_PATH'):
        if IS_WINDOWS:
            _BGMI_PATH = os.path.join(os.environ.get('USERPROFILE', None), '.bgmi')
        else:
            _BGMI_PATH = os.path.join(os.environ.get('HOME', '/tmp'), '.bgmi')
    else:  # pragma: no cover
        _BGMI_PATH = os.environ.get('BGMI_PATH')
    return _BGMI_PATH


BGMI_PATH = get_bgmi_path()
if not BGMI_PATH:  # pragma: no cover
    raise SystemExit

# DB_URL = os.path.join(BGMI_PATH, 'bangumi.db')
DB_URL = 'sqlite:///{}'.format(os.path.join(BGMI_PATH, 'bangumi.db'))
KV_DB_PATH = os.path.join(BGMI_PATH, 'kv.db')
CONFIG_FILE_PATH = os.path.join(BGMI_PATH, 'bgmi.cfg')

# SCRIPT_DB_URL = 'sqlite:///{}'.format(os.path.join(BGMI_PATH, 'script.db'))
SCRIPT_PATH = os.path.join(BGMI_PATH, 'scripts')
TOOLS_PATH = os.path.join(BGMI_PATH, 'tools')


def read_config():
    c = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE_PATH):
        write_default_config()
        return
    c.read(CONFIG_FILE_PATH)

    for i in __writeable__:
        if c.has_option('bgmi', i):
            globals().update({i: c.get('bgmi', i)})

    for i in DOWNLOAD_DELEGATE_MAP.get(DOWNLOAD_DELEGATE, []):
        if c.has_option(DOWNLOAD_DELEGATE, i):
            globals().update({i: c.get(DOWNLOAD_DELEGATE, i)})


def print_config():
    c = configparser.ConfigParser()

    c.read(CONFIG_FILE_PATH)
    string = ''
    string += '[bgmi]\n'
    for i in __writeable__:
        string += '{0}={1}\n'.format(i, c.get('bgmi', i))

    string += '\n[{0}]\n'.format(DOWNLOAD_DELEGATE)
    for i in DOWNLOAD_DELEGATE_MAP.get(DOWNLOAD_DELEGATE, []):
        string += '{0}={1}\n'.format(i, c.get(DOWNLOAD_DELEGATE, i))
    return string


def write_default_config():
    c = configparser.ConfigParser()
    if not c.has_section('bgmi'):
        c.add_section('bgmi')

    for k in __writeable__:
        v = globals().get(k, '0')
        if k == 'ADMIN_TOKEN' and v is None:
            v = hashlib.md5(str(random.random()).encode('utf-8')).hexdigest()

        c.set('bgmi', k, v)

    if DOWNLOAD_DELEGATE not in DOWNLOAD_DELEGATE_MAP.keys():
        raise Exception(DOWNLOAD_DELEGATE)

    if not c.has_section(DOWNLOAD_DELEGATE):
        c.add_section(DOWNLOAD_DELEGATE)

    for k in DOWNLOAD_DELEGATE_MAP.get(DOWNLOAD_DELEGATE, []):
        v = globals().get(k, None)
        c.set(DOWNLOAD_DELEGATE, k, v)

    try:
        with open(CONFIG_FILE_PATH, 'w') as f:
            c.write(f)
    except IOError:  # pragma: no cover
        print('[-] Error writing to config file and ignored')


def write_config(config=None, value=None):
    if not os.path.exists(CONFIG_FILE_PATH):
        write_default_config()
        return {
            'status': 'error',
            'message':
            'Config file does not exists, writing default config file',
            'data': []
        }

    c = configparser.ConfigParser()
    c.read(CONFIG_FILE_PATH)

    try:
        if config is None:
            result = {'status': 'info', 'message': print_config()}

        elif value is None:  # config(config, None)
            result = {'status': 'info'}

            if config in __download_delegate__:
                result['message'] = '{0}={1}'.format(config, c.get(DOWNLOAD_DELEGATE, config))
            else:
                result['message'] = '{0}={1}'.format(config, c.get('bgmi', config))

        else:  # config(config, Value)
            if config in __writeable__:
                if config == 'DOWNLOAD_DELEGATE' and value not in DOWNLOAD_DELEGATE_MAP:
                    return {
                        'status':
                        'error',
                        'message':
                        '{0} is not a support download_delegate'.format(value)
                    }
                c.set('bgmi', config, value)
                with open(CONFIG_FILE_PATH, 'w') as f:
                    c.write(f)
                read_config()
                if config == 'DOWNLOAD_DELEGATE' and not c.has_section(DOWNLOAD_DELEGATE):
                    c.add_section(DOWNLOAD_DELEGATE)
                    for i in DOWNLOAD_DELEGATE_MAP[DOWNLOAD_DELEGATE]:
                        v = globals().get(i, '')
                        c.set(DOWNLOAD_DELEGATE, i, v)

                    with open(CONFIG_FILE_PATH, 'w') as f:
                        c.write(f)
                result = {
                    'status': 'success',
                    'message': '{0} has been set to {1}'.format(config, value)
                }

            elif config in DOWNLOAD_DELEGATE_MAP.get(DOWNLOAD_DELEGATE):
                c.set(DOWNLOAD_DELEGATE, config, value)
                with open(CONFIG_FILE_PATH, 'w') as f:
                    c.write(f)
                result = {
                    'status': 'success',
                    'message': '{0} has been set to {1}'.format(config, value)
                }
            else:
                result = {
                    'status': 'error',
                    'message':
                    '{0} does not exist or not writeable'.format(config)
                }

    except (configparser.NoOptionError, configparser.NoSectionError):
        write_default_config()
        result = {
            'status': 'error',
            'message': 'Error in config file, try rerun `bgmi config`'
        }

    return result


# --------- Writeable ---------- #
# Setting bangumi.moe url
BANGUMI_MOE_URL = 'https://bangumi.moe'

# Setting share.dmhy.org url
SHARE_DMHY_URL = 'https://share.dmhy.org'

DISABLED_DATA_SOURCE = ''

# BGmi user path
SAVE_PATH = os.path.join(BGMI_PATH, 'bangumi')
FRONT_STATIC_PATH = os.path.join(BGMI_PATH, 'front_static')

# admin token
ADMIN_TOKEN = None

# temp path
TMP_PATH = os.path.join(BGMI_PATH, 'tmp')

# log path
LOG_PATH = os.path.join(TMP_PATH, 'bgmi.log')

# Download delegate
DOWNLOAD_DELEGATE = 'aria2-rpc'

# danmaku api url, https://github.com/DIYgod/DPlayer#related-projects
DANMAKU_API_URL = ''

# language
LANG = 'zh_cn'

# max page
MAX_PAGE = '3'

# aria2
ARIA2_RPC_URL = 'http://localhost:6800/rpc'
ARIA2_RPC_TOKEN = 'token:'

# deluge
DELUGE_RPC_URL = 'http://127.0.0.1:8112/json'
DELUGE_RPC_PASSWORD = 'deluge'

# transmission-rpc
TRANSMISSION_RPC_URL = '127.0.0.1'
TRANSMISSION_RPC_PORT = '9091'
TRANSMISSION_RPC_USERNAME = 'your_username'
TRANSMISSION_RPC_PASSWORD = 'your_password'

# tag of bangumi on bangumi.moe
BANGUMI_TAG = '549ef207fe682f7549f1ea90'

# Global blocked keyword
GLOBAL_FILTER = 'Leopard-Raws, hevc, x265, c-a Raws'

# enable global filter
ENABLE_GLOBAL_FILTER = '1'

# use tornado serving video files
TORNADO_SERVE_STATIC_FILES = '0'

# ------------------------------ #
# !!! Read config from file and write to globals() !!!
read_config()
# ------------------------------ #
# will be used in other other models
__all_writable_now__ = __writeable__ + DOWNLOAD_DELEGATE_MAP[DOWNLOAD_DELEGATE]

# --------- Read-Only ---------- #

# Detail URL
# platform
IS_WINDOWS = platform.system() == 'Windows'
