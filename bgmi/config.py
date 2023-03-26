import os
import pathlib
import platform
import secrets
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import strenum
import tomli
import tomli_w
from pydantic import BaseSettings, Field, HttpUrl


class Source(strenum.StrEnum):
    Mikan = "mikan_project"
    BangumiMoe = "bangumi_moe"
    Dmhy = "dmhy"


IS_WINDOWS = platform.system() == "Windows"


def get_bgmi_home() -> Path:
    h = os.environ.get("BGMI_PATH")

    if h:
        return Path(h)

    if IS_WINDOWS:
        home_dir = os.environ.get("USERPROFILE") or os.environ.get("HOME") or tempfile.gettempdir()
        return Path(home_dir).joinpath(".bgmi")

    return Path(os.environ.get("HOME", "/tmp")).joinpath(".bgmi")


BGMI_PATH = get_bgmi_home()

CONFIG_FILE_PATH = BGMI_PATH / "config.toml"


class Aria2Config(BaseSettings):
    # aria2
    ARIA2_RPC_URL = "http://localhost:6800/rpc"
    ARIA2_RPC_TOKEN = "token:"


class TransmissionConfig(BaseSettings):
    # transmission-rpc
    TRANSMISSION_RPC_URL = "127.0.0.1"
    TRANSMISSION_RPC_PORT = "9091"
    TRANSMISSION_RPC_USERNAME = "your_username"
    TRANSMISSION_RPC_PASSWORD = "your_password"
    TRANSMISSION_RPC_PATH = "/transmission/"


class QBittorrentConfig(BaseSettings):
    QBITTORRENT_HOST = "127.0.0.1"
    QBITTORRENT_PORT = "8080"
    QBITTORRENT_USERNAME = "admin"
    QBITTORRENT_PASSWORD = "adminadmin"
    QBITTORRENT_CATEGORY = ""


class DelugeConfig(BaseSettings):
    DELUGE_RPC_URL = "http://127.0.0.1:8112/json"
    DELUGE_RPC_PASSWORD = "deluge"


class Config(BaseSettings):
    TMP_PATH: Path = BGMI_PATH.joinpath("tmp")
    LOG_PATH = TMP_PATH.joinpath("bgmi.log")

    SAVE_PATH: Path = Field(BGMI_PATH.joinpath("bangumi"), description="bangumi save path")
    FRONT_STATIC_PATH: Path = BGMI_PATH.joinpath("front_static")

    DB_PATH: pathlib.Path
    SCRIPT_DB_PATH: pathlib.Path
    SCRIPT_PATH: pathlib.Path
    TOOLS_PATH: pathlib.Path

    MAX_PAGE: int = 3

    ENABLE_GLOBAL_FILTER: bool = Field(True, description="enable global filter")

    TORNADO_SERVE_STATIC_FILES: bool = Field(False, description="use tornado serving video files")

    BANGUMI_MOE_URL: HttpUrl = Field(HttpUrl("https://bangumi.moe"), description="Setting bangumi.moe url")
    SHARE_DMHY_URL: HttpUrl = Field(HttpUrl("https://share.dmhy.org"), description="Setting share.dmhy.org url")
    DATA_SOURCE: Source = Field(Source.BangumiMoe, description="data source")  # type: ignore

    # admin token
    ADMIN_TOKEN: str = Field(default_factory=lambda: secrets.token_urlsafe(12), description="webui admin token")

    # Download delegate
    DOWNLOAD_DELEGATE = "aria2-rpc"

    DANMAKU_API_URL: str = Field(description="danmaku api url, https://github.com/DIYgod/DPlayer#related-projects")

    # language
    LANG: str = "zh_cn"

    # deluge
    DELUGE_RPC_URL = "http://127.0.0.1:8112/json"
    DELUGE_RPC_PASSWORD = "deluge"

    # path of wget
    WGET_PATH = "/usr/bin/wget"

    aria2: Aria2Config = Aria2Config()
    transmission: TransmissionConfig = TransmissionConfig()
    qbittorrent: QBittorrentConfig = QBittorrentConfig()
    deluge: DelugeConfig = DelugeConfig()

    GLOBAL_FILTER: List[str] = Field(
        ["Leopard-Raws", "hevc", "x265", "c-a Raws", "U3-Web"], description="Global exclude keywords"
    )

    class Config:
        validate_assignment = True


if CONFIG_FILE_PATH.exists():
    cfg = Config.parse_obj(tomli.loads(CONFIG_FILE_PATH.read_text()))
else:
    cfg = Config()


def print_config() -> str:
    return tomli_w.dumps(cfg.dict())


def write_default_config() -> None:
    CONFIG_FILE_PATH.write_text(tomli_w.dumps(Config().dict()), encoding="utf8")


def write_config(key: Optional[str] = None, value: Optional[str] = None) -> Dict[str, Any]:
    if not CONFIG_FILE_PATH.exists():
        CONFIG_FILE_PATH.write_text(tomli_w.dumps(Config().dict()), encoding="utf8")
        return {
            "status": "error",
            "message": "Config file does not exists, writing default config file. please try again",
            "data": [],
        }
    #
    # result = {}  # type: Dict[str, Any]
    # try:
    #     if c is None:
    #         result = {"status": "info", "message": print_config()}
    #
    #     elif value is None:  # config(config, None)
    #         result = {"status": "info"}
    #
    #         if c in __download_delegate__:
    #             result["message"] = f"{c}={c.get(DOWNLOAD_DELEGATE, c)}"
    #         else:
    #             result["message"] = "{}={}".format(c, c.get("bgmi", c))
    #
    #     else:  # config(config, Value)
    #         if c in __writeable__:
    #             c.set("bgmi", c, value)
    #             with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
    #                 c.write(f)
    #
    #             read_config()
    #             if c == "DOWNLOAD_DELEGATE" and not c.has_section(DOWNLOAD_DELEGATE):
    #                 c.add_section(DOWNLOAD_DELEGATE)
    #                 for i in DOWNLOAD_DELEGATE_MAP.get(DOWNLOAD_DELEGATE, []):
    #                     v = globals().get(i, "")
    #                     c.set(DOWNLOAD_DELEGATE, i, v)
    #
    #                 with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
    #                     c.write(f)
    #
    #             result = {
    #                 "status": "success",
    #                 "message": f"{c} has been set to {value}",
    #             }
    #
    #         elif c in DOWNLOAD_DELEGATE_MAP.get(DOWNLOAD_DELEGATE, []):
    #             c.set(DOWNLOAD_DELEGATE, c, value)
    #             with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
    #                 c.write(f)
    #
    #             result = {
    #                 "status": "success",
    #                 "message": f"{c} has been set to {value}",
    #             }
    #         else:
    #             result = {
    #                 "status": "error",
    #                 "message": f"{c} does not exist or not writeable",
    #             }
    #
    # except configparser.NoOptionError:
    #     write_default_config()
    #     result = {
    #         "status": "error",
    #         "message": "Error in config file, try rerun `bgmi config`",
    #     }
    #
    # result["data"] = [{"writable": True, "name": x, "value": globals()[x]} for x in __writeable__] + [
    #     {"writable": False, "name": x, "value": globals()[x]} for x in __readonly__
    # ]
    # return result


if __name__ == "__main__":
    write_default_config()
