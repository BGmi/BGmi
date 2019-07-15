import configparser
import hashlib
import os
import platform
import random
import tempfile
from functools import wraps

import chardet

# --------- Read-Only ---------- #

# Detail URL
# platform
IS_WINDOWS = platform.system() == 'Windows'
SHOW_WARNING = bool(os.getenv('DEV') or os.getenv('DEBUG'))
SOURCE_ROOT = os.path.dirname(__file__)

# ------- Read-Only End -------- #

# download delegate
__transmission__ = (
    'TRANSMISSION_RPC_URL',
    'TRANSMISSION_RPC_PORT',
    'TRANSMISSION_RPC_USERNAME',
    'TRANSMISSION_RPC_PASSWORD',
)
__aria2__ = ('ARIA2_RPC_URL', 'ARIA2_RPC_TOKEN')
__deluge__ = ('DELUGE_RPC_URL', 'DELUGE_RPC_PASSWORD')

__download_delegate__ = __aria2__ + __transmission__ + __deluge__

# fake __all__
__all__ = (
    'BANGUMI_MOE_URL',
    'SAVE_PATH',
    'DOWNLOAD_DELEGATE',
    'DB_URL',
    'MAX_PAGE',
    'TMP_PATH',
    'LOG_LEVEL',
    'SOURCE_ROOT',
    'DANMAKU_API_URL',
    'DISABLED_DATA_SOURCE',
    'LANG',
    'FRONT_STATIC_PATH',
    'ADMIN_TOKEN',
    'SHARE_DMHY_URL',
    'GLOBAL_FILTER',
    'ENABLE_GLOBAL_FILTER',
    'TORNADO_SERVE_STATIC_FILES',
    'KEYWORDS_WEIGHT',
)

# cannot be rewrite
__readonly__ = (
    'KEYWORDS_WEIGHT',
    'SHOW_WARNING',
    'BGMI_PATH',
    'SOURCE_ROOT',
    'CONFIG_FILE_PATH',
    'TOOLS_PATH',
    'SCRIPT_PATH',
    'FRONT_STATIC_PATH',
)

# writeable
__writeable__ = tuple(i for i in __all__ if i not in __readonly__)

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
            _BGMI_PATH = os.path.join(os.environ.get('HOME', tempfile.mkdtemp()), '.bgmi')
    else:  # pragma: no cover
        _BGMI_PATH = os.environ.get('BGMI_PATH')
    return _BGMI_PATH


BGMI_PATH = get_bgmi_path()
if not BGMI_PATH:  # pragma: no cover
    exit(1)

DB_URL = f'sqlite:///{os.path.join(BGMI_PATH, "bangumi.db")}'
CONFIG_FILE_PATH = os.path.join(BGMI_PATH, 'bgmi.cfg')

# SCRIPT_DB_URL = 'sqlite:///{}'.format(os.path.join(BGMI_PATH, 'script.db'))
SCRIPT_PATH = os.path.join(BGMI_PATH, 'scripts')
TOOLS_PATH = os.path.join(BGMI_PATH, 'tools')


def get_config_parser_and_read() -> configparser.ConfigParser:
    with open(CONFIG_FILE_PATH, 'rb') as f:
        content = f.read()
        encoding = chardet.detect(content).get('encoding')

    c = configparser.ConfigParser()
    c.read_string(content.decode(encoding))
    return c


def write_config_parser(config_parser: configparser.ConfigParser):
    try:
        with open(CONFIG_FILE_PATH, 'rb+') as f:
            encoding = chardet.detect(f.read()).get('encoding')
            if encoding == 'ascii':
                encoding = 'utf-8'
    except IOError:
        encoding = None
    with open(CONFIG_FILE_PATH, 'w+', encoding=encoding) as f:
        config_parser.write(f)


def read_config_from_env():
    for key, value in os.environ.items():
        if key.startswith('BGMI_'):
            real_key = key.replace('BGMI_', '')
            if real_key in __all__ or real_key in __download_delegate__:
                globals().update({real_key: value})


def read_config():
    if not os.path.exists(CONFIG_FILE_PATH):
        write_default_config()
        return

    c = get_config_parser_and_read()
    for i in __writeable__:
        if c.has_option('bgmi', i):
            v = c.get('bgmi', i)
            if v:
                globals().update({i: v})

    for i in DOWNLOAD_DELEGATE_MAP.get(DOWNLOAD_DELEGATE, []):
        if c.has_option(DOWNLOAD_DELEGATE, i):
            v = c.get(DOWNLOAD_DELEGATE, i)
            if v:
                globals().update({i: v})

    read_keywords_weight_section(c)


def read_keywords_weight_section(c: configparser.ConfigParser):
    section = 'keyword weight'
    try:
        KEYWORDS_WEIGHT.update(dict(c.items(section)))
        for key, value in c.items(section):
            try:
                KEYWORDS_WEIGHT[key] = int(value)
            except ValueError:
                print(
                    f'value of keyword.{key} can\'t be "{value}",'
                    ' it must be a int, ignore this line in config file'
                )
    except configparser.NoSectionError:
        c.add_section(section)
        write_config_parser(c)


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
        write_config_parser(c)
    except IOError:  # pragma: no cover
        print('[-] Error writing to config file and ignored')


def _config_decorator(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (configparser.NoOptionError, configparser.NoSectionError):
            write_default_config()
            result = {
                'status': 'error',
                'message': 'Error in config file, try rerun `bgmi config`',
            }
        except FileNotFoundError:
            write_default_config()
            result = {
                'status': 'error',
                'message': 'Config file does not exists, writing default config file',
                'data': [],
            }
        return result

    return wrapped


@_config_decorator
def print_config():
    get_config_parser_and_read()
    string = ''
    string += '[bgmi]\n'
    for i in __writeable__:
        string += '{}={}\n'.format(i, globals().get(i))

    string += f'\n[{DOWNLOAD_DELEGATE}]\n'
    for i in DOWNLOAD_DELEGATE_MAP.get(DOWNLOAD_DELEGATE, []):
        string += '{}={}\n'.format(i, globals().get(i))

    string += '\n[{}]'.format('keyword weight')
    for key, value in KEYWORDS_WEIGHT.items():
        string += f'{key}={value}\n'

    return {'status': 'success', 'message': string}


@_config_decorator
def print_config_key(config):
    c = get_config_parser_and_read()

    if config in __download_delegate__:
        s = '{}={}'.format(config, c.get(DOWNLOAD_DELEGATE, config))
    else:
        s = '{}={}'.format(config, c.get('bgmi', config))
    return {'status': 'success', 'message': s}


@_config_decorator
def write_config(config, value):
    c = get_config_parser_and_read()

    if config in __writeable__:
        if config == 'DOWNLOAD_DELEGATE' and value not in DOWNLOAD_DELEGATE_MAP:
            return {'status': 'error', 'message': f'{value} is not a support download_delegate'}
        c.set('bgmi', config, value)
        write_config_parser(c)
        read_config()
        if config == 'DOWNLOAD_DELEGATE' and not c.has_section(DOWNLOAD_DELEGATE):
            c.add_section(DOWNLOAD_DELEGATE)
            for i in DOWNLOAD_DELEGATE_MAP[DOWNLOAD_DELEGATE]:
                v = globals().get(i, '')
                c.set(DOWNLOAD_DELEGATE, i, v)

            write_config_parser(c)
        result = {
            'status': 'success',
            'message': f'{config} has been set to {value}',
        }

    elif config in DOWNLOAD_DELEGATE_MAP.get(DOWNLOAD_DELEGATE):
        c.set(DOWNLOAD_DELEGATE, config, value)
        write_config_parser(c)
        result = {
            'status': 'success',
            'message': f'{config} has been set to {value}',
        }
    else:
        result = {
            'status': 'error',
            'message': f'{config} does not exist or not writeable',
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

LOG_LEVEL = 'info'
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
TRANSMISSION_RPC_URL = 'http://:@127.0.0.1:9091/transmission/rpc'

# tag of bangumi on bangumi.moe
BANGUMI_TAG = '549ef207fe682f7549f1ea90'

# Global blocked keyword
GLOBAL_FILTER = 'Leopard-Raws, hevc, x265, c-a Raws, 预告'

# enable global filter
ENABLE_GLOBAL_FILTER = '1'

# use tornado serving video files
TORNADO_SERVE_STATIC_FILES = '0'

KEYWORDS_WEIGHT = {}

# ------------------------------ #
# !!! Read config from file and write to globals() !!!
read_config()
read_config_from_env()
# ------------------------------ #
# will be used in other other db_models
__all_writable_now__ = __writeable__ + DOWNLOAD_DELEGATE_MAP[DOWNLOAD_DELEGATE]
