import enum
import os
import platform
import secrets
import string
import tempfile
from typing import Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, Extra, Field, validator


class DownloadDelegateEnum(str, enum.Enum):
    Aria2RPC: str = 'aria2-rpc'
    TransmissionRPC: str = 'transmission-rpc'
    DelugeRPC: str = 'deluge-rpc'

    def __str__(self):
        return self.value


alphabet = string.ascii_letters + string.digits


def get_bgmi_path():
    p = os.path.normpath(os.environ.get('BGMI_PATH', os.path.expanduser('~/.bgmi')))
    if not p:
        p = tempfile.mkdtemp()
        print('$HOME and $BGMI_PATH not set, use a tmp dir ' + p)
    return p


class WritableConfig(BaseSettings):
    DOWNLOAD_DELEGATE: DownloadDelegateEnum = DownloadDelegateEnum.Aria2RPC
    DANMAKU_API_URL: Optional[str]
    LANG: str = 'zh_cn'
    MAX_PAGE: int = 3

    # enable global filter
    ENABLE_GLOBAL_FILTER: bool = True

    # Global blocked keyword
    GLOBAL_FILTER: List[str] = ['Leopard-Raws', 'hevc', 'x265', 'c-a Raws', 'U3-Web']

    # use tornado serving video files
    TORNADO_SERVE_STATIC_FILES: bool = False
    KEYWORDS_WEIGHT: Dict[str, int] = Field(
        {},
        alias='keyword weight',
        env='keyword weight',
    )
    ADMIN_TOKEN: str = ''.join(secrets.choice(alphabet) for i in range(16))
    DISABLED_DATA_SOURCE: List[str] = []

    # log path
    LOG_PATH = os.path.join(tempfile.mkdtemp(), 'bgmi.log')

    LOG_LEVEL = 'info'

    # config for aria2

    ARIA2_RPC_URL: AnyHttpUrl = 'http://127.0.0.1:6800/rpc'  # type: ignore
    ARIA2_RPC_TOKEN: str = 'token:'

    # transmission-rpc
    TRANSMISSION_RPC_URL: AnyHttpUrl = 'http://127.0.0.1:9091/transmission/rpc'  # type: ignore

    # deluge
    DELUGE_RPC_URL: AnyHttpUrl = 'http://127.0.0.1:8112/json'  # type: ignore
    DELUGE_RPC_PASSWORD: str = 'deluge'

    BGMI_PATH: str = get_bgmi_path()
    SAVE_PATH: str = os.path.join(BGMI_PATH, 'bangumi')

    @validator('ARIA2_RPC_URL')
    def aria2_url_not_ends_with_json_rpc(cls, v: str):
        if v.endswith('/jsonrpc'):
            raise ValueError('ARIA2_RPC_URL should be xml-rpc end-point not json-rpc end-point')
        return v

    @validator('ARIA2_RPC_TOKEN')
    def aria2_rpc_token_must_starts_with_token(cls, v: str):
        if not v.startswith('token:'):
            raise ValueError('ARIA2_RPC_TOKEN must starts with `token:`')
        return v

    @validator('GLOBAL_FILTER', 'DISABLED_DATA_SOURCE', pre=True, always=True, whole=True)
    def name_must_contain_space(cls, v: Union[str, list]):
        if isinstance(v, list):
            return v
        return [s.strip() for s in v.split(',')]

    class Config:
        env_prefix = 'BGMI_'
        extra = Extra.ignore


class Config(WritableConfig):
    """user defined in ``$BGMI_PATH/bgmi.cfg``"""

    # DB_PATH: str = os.path.join(BGMI_PATH, 'bangumi.db')

    BANGUMI_TAG: str = '549ef207fe682f7549f1ea90'

    IS_WINDOWS = platform.system() == 'Windows'
    SHOW_WARNING = bool(os.getenv('DEV') or os.getenv('DEBUG'))
    #: path of bgmi path, not project path
    SOURCE_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

    @property
    def DB_PATH(self):
        return os.path.join(self.BGMI_PATH, 'bangumi.db')

    @property
    def CONFIG_FILE_PATH(self):
        return os.path.join(self.BGMI_PATH, 'bgmi.cfg')

    @property
    def TOOLS_PATH(self):
        return os.path.join(self.BGMI_PATH, 'tools')

    @property
    def SCRIPT_PATH(self):
        return os.path.join(self.BGMI_PATH, 'scripts')

    @property
    def FRONT_STATIC_PATH(self):
        return os.path.join(self.BGMI_PATH, 'front_static')

    @property
    def TMP_PATH(self):
        return os.path.join(self.BGMI_PATH, 'tmp')


class AdvancedConfig(BaseSettings):
    """user defined in ``$BGMI_PATH/advanced_config.toml``"""

    #: default value will by sqlite in ``$BGMI_PATH/bangumi.db``
    DB_URL: Optional[str]

    class Config:
        env_prefix = 'BGMI_'
        extra = Extra.ignore
