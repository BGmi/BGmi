import json
import os
import pathlib
import platform
import secrets
import tempfile
from pathlib import Path
from typing import List

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
    TRANSMISSION_RPC_URL: str = "127.0.0.1"
    TRANSMISSION_RPC_PORT: int = 9091
    TRANSMISSION_RPC_USERNAME: str = "your_username"
    TRANSMISSION_RPC_PASSWORD: str = "your_password"
    TRANSMISSION_RPC_PATH: str = "/transmission/"


class QBittorrentConfig(BaseSettings):
    QBITTORRENT_HOST: str = "127.0.0.1"
    QBITTORRENT_PORT: int = 8080
    QBITTORRENT_USERNAME: str = "admin"
    QBITTORRENT_PASSWORD: str = "adminadmin"
    QBITTORRENT_CATEGORY: str = ""


class DelugeConfig(BaseSettings):
    DELUGE_RPC_URL: HttpUrl = "http://127.0.0.1:8112/json"  # type: ignore
    DELUGE_RPC_PASSWORD: str = "deluge"


class Config(BaseSettings):
    TMP_PATH: Path = BGMI_PATH.joinpath("tmp")
    LOG_PATH = TMP_PATH.joinpath("bgmi.log")

    SAVE_PATH: Path = Field(BGMI_PATH.joinpath("bangumi"), description="bangumi save path")
    FRONT_STATIC_PATH: Path = BGMI_PATH.joinpath("front_static")

    DB_PATH: pathlib.Path = BGMI_PATH.joinpath("bangumi.db")
    SCRIPT_DB_PATH: pathlib.Path = BGMI_PATH.joinpath("bangumi-scripts.db")
    SCRIPT_PATH: pathlib.Path = BGMI_PATH.joinpath("scripts")
    TOOLS_PATH: pathlib.Path = BGMI_PATH.joinpath("tools")

    MAX_PAGE: int = 3

    ENABLE_GLOBAL_FILTER: bool = Field(True, description="enable global filter")

    TORNADO_SERVE_STATIC_FILES: bool = Field(False, description="use tornado serving video files")

    BANGUMI_MOE_URL: HttpUrl = Field("https://bangumi.moe", description="Setting bangumi.moe url")  # type: ignore
    SHARE_DMHY_URL: HttpUrl = Field("https://share.dmhy.org", description="Setting share.dmhy.org url")  # type: ignore
    DATA_SOURCE: Source = Field(Source.BangumiMoe, description="data source")  # type: ignore

    # admin token
    ADMIN_TOKEN: str = Field(default_factory=lambda: secrets.token_urlsafe(12), description="webui admin token")

    # Download delegate
    DOWNLOAD_DELEGATE = "aria2-rpc"

    DANMAKU_API_URL: str = Field("", description="danmaku api url, https://github.com/DIYgod/DPlayer#related-projects")

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

    def save(self) -> None:
        CONFIG_FILE_PATH.write_text(tomli_w.dumps(json.loads(self.json())), encoding="utf8")


if CONFIG_FILE_PATH.exists():
    cfg = Config.parse_obj(tomli.loads(CONFIG_FILE_PATH.read_text()))
else:
    cfg = Config()


def print_config() -> str:
    return tomli_w.dumps(json.loads(cfg.json()))


def write_default_config() -> None:
    Config().save()


if __name__ == "__main__":
    write_default_config()
