import json
import os
import pathlib
import platform
import secrets
import tempfile
from pathlib import Path
from typing import List

import pydantic
import strenum
import tomli
import tomli_w
from pydantic import BaseSettings, Extra, Field, HttpUrl


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


class BaseSetting(BaseSettings):
    class Config:
        validate_assignment = True
        extra = Extra.ignore


class Aria2Config(BaseSetting):
    rpc_url = "http://localhost:6800/rpc"
    rpc_token = "token:"


class TransmissionConfig(BaseSetting):
    rpc_url: str = "127.0.0.1"
    rpc_port: int = 9091
    rpc_username: str = "your_username"
    rpc_password: str = "your_password"
    rpc_path: str = "/transmission/"


class QBittorrentConfig(BaseSetting):
    rpc_host: str = "127.0.0.1"
    rpc_port: int = 8080
    rpc_username: str = "admin"
    rpc_password: str = "adminadmin"
    category: str = ""


class DelugeConfig(BaseSetting):
    rpc_url: HttpUrl = "http://127.0.0.1:8112/json"  # type: ignore
    rpc_password: str = "deluge"


class Config(BaseSetting):
    data_source: Source = Field(Source.BangumiMoe, description="data source")  # type: ignore
    download_delegate: str = Field("aria2-rpc", description="download delegate")

    tmp_path: Path = BGMI_PATH.joinpath("tmp")
    log_path = tmp_path.joinpath("bgmi.log")

    save_path: Path = Field(BGMI_PATH.joinpath("bangumi"), description="bangumi save path")
    front_static_path: Path = BGMI_PATH.joinpath("front_static")

    db_path: pathlib.Path = BGMI_PATH.joinpath("bangumi.db")
    script_path: pathlib.Path = BGMI_PATH.joinpath("scripts")
    tools_path: pathlib.Path = BGMI_PATH.joinpath("tools")

    max_path: int = 3

    serve_static_files: bool = Field(False, description="use tornado serving video files")

    bangumi_moe_url: HttpUrl = Field("https://bangumi.moe", description="Setting bangumi.moe url")  # type: ignore
    share_dmhy_url: HttpUrl = Field("https://share.dmhy.org", description="Setting share.dmhy.org url")  # type: ignore

    # admin token
    admin_token: str = Field(default_factory=lambda: secrets.token_urlsafe(12), description="webui admin token")

    danmaku_api_url: str = Field("", description="danmaku api url, https://github.com/DIYgod/DPlayer#related-projects")

    # language
    lang: str = "zh_cn"

    aria2: Aria2Config = Aria2Config()
    transmission: TransmissionConfig = TransmissionConfig()
    qbittorrent: QBittorrentConfig = QBittorrentConfig()
    deluge: DelugeConfig = DelugeConfig()

    enable_global_filters: bool = Field(True, description="enable global filter")
    global_filters: List[str] = Field(
        ["Leopard-Raws", "hevc", "x265", "c-a Raws", "U3-Web"], description="Global exclude keywords"
    )

    def save(self) -> None:
        CONFIG_FILE_PATH.write_text(tomli_w.dumps(json.loads(self.json())), encoding="utf8")


if CONFIG_FILE_PATH.exists():
    try:
        cfg = Config.parse_obj(tomli.loads(CONFIG_FILE_PATH.read_text()))
    except pydantic.ValidationError as e:
        print("配置文件错误，请手动编辑配置文件后重试")
        print("配置文件位置：", CONFIG_FILE_PATH)
        print(e)
        raise SystemExit
else:
    cfg = Config()


def print_config() -> str:
    return tomli_w.dumps(json.loads(cfg.json()))


def write_default_config() -> None:
    if not CONFIG_FILE_PATH.exists():
        Config().save()


if __name__ == "__main__":
    write_default_config()
