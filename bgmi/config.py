import configparser
import os
from functools import wraps
from io import StringIO
from typing import Dict

import toml

from bgmi.config_utils import (
    dump_config, get_config_parser_and_read, load_config, write_config_parser
)
from bgmi.models.config import AdvancedConfig, Config, WritableConfig

# --------- Read-Only ---------- #
DEFAULT_CONFIG = Config()

# ------- Read-Only End -------- #
# download delegate
__transmission__ = ('TRANSMISSION_RPC_URL', )
__aria2__ = ('ARIA2_RPC_URL', 'ARIA2_RPC_TOKEN')
__deluge__ = ('DELUGE_RPC_URL', 'DELUGE_RPC_PASSWORD')

__download_delegate__ = __aria2__ + __transmission__ + __deluge__

# fake __all__
__fake_all__ = (
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
    'ADMIN_TOKEN',
    'GLOBAL_FILTER',
    'ENABLE_GLOBAL_FILTER',
    'TORNADO_SERVE_STATIC_FILES',
    'KEYWORDS_WEIGHT',
) + __download_delegate__

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
__writeable__ = tuple(i for i in __fake_all__ if i not in __readonly__)

# the real __all__
__all__ = list(__fake_all__ + __download_delegate__ + __readonly__)

DOWNLOAD_DELEGATE_MAP: Dict[str, tuple] = {
    'aria2-rpc': __aria2__,
    'transmission-rpc': __transmission__,
    'deluge-rpc': __deluge__,
}

CONFIG_FILE_PATH = os.path.join(Config().BGMI_PATH, 'bgmi.cfg')


def write_default_config():
    c = dump_config(WritableConfig.parse_obj(DEFAULT_CONFIG.dict(by_alias=True)))

    try:
        write_config_parser(c, CONFIG_FILE_PATH)
    except OSError:  # pragma: no cover
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
    get_config_parser_and_read(CONFIG_FILE_PATH)
    with StringIO() as f:
        dump_config(config_obj).write(f)
        f.seek(0)
        content = f.read()
    return {'status': 'success', 'message': content}


@_config_decorator
def print_config_key(config):
    c = get_config_parser_and_read(CONFIG_FILE_PATH)
    s = '{}={}'.format(config, c.get('bgmi', config))
    return {'status': 'success', 'message': s}


@_config_decorator
def write_config(config, value):
    c = get_config_parser_and_read(CONFIG_FILE_PATH)

    if config in __writeable__:
        if config == 'DOWNLOAD_DELEGATE' and value not in DOWNLOAD_DELEGATE_MAP:
            return {'status': 'error', 'message': f'{value} is not a support download_delegate'}
        c.set('bgmi', config, value)
        write_config_parser(c, CONFIG_FILE_PATH)
        read_config()
        if config == 'DOWNLOAD_DELEGATE':
            c.set('bgmi', config, value)
            write_config_parser(c, CONFIG_FILE_PATH)
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


# ------------------------------ #
# will be used in other other db_models
__admin_version__ = '1.1.x'

if 'SYSTEM_TEAMFOUNDATIONSERVERURI' in os.environ:
    # in azure pipelines
    NPM_REGISTER_DOMAIN = 'registry.npmjs.com'
else:
    NPM_REGISTER_DOMAIN = 'registry.npm.taobao.org'

FRONTEND_NPM_URL = f'https://{NPM_REGISTER_DOMAIN}/bgmi-frontend/'
PACKAGE_JSON_URL = FRONTEND_NPM_URL + __admin_version__


def read_config() -> Config:
    # raise Exception(load_config(get_config_parser_and_read(CONFIG_FILE_PATH)))
    return Config.parse_obj(load_config(get_config_parser_and_read(CONFIG_FILE_PATH)))


try:
    config_obj = read_config()
except OSError:
    config_obj = Config()

try:
    with open(os.path.join(Config().SAVE_PATH, 'advanced_config.toml'), encoding='utf-8') as ff:
        advanced_config_obj = AdvancedConfig.parse_obj(toml.load(ff))
except OSError:
    advanced_config_obj = AdvancedConfig()
