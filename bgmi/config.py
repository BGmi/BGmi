import json
import os
import pathlib
import platform
import secrets
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, cast

import pydantic
import strenum
import tomlkit
from pydantic import BaseModel, Extra, Field, HttpUrl


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


BGMI_PATH = get_bgmi_home().absolute()

CONFIG_FILE_PATH = BGMI_PATH / "config.toml"


class BaseSetting(BaseModel):
    class Config:
        validate_assignment = True
        extra = Extra.ignore


class Aria2Config(BaseSetting):
    rpc_url = os.getenv("BGMI_ARIA2_RPC_URL") or "http://127.0.0.1:6800/rpc"
    rpc_token = os.getenv("BGMI_ARIA2_RPC_TOKEN") or "token:"


class TransmissionConfig(BaseSetting):
    rpc_host: str = os.getenv("BGMI_TRANSMISSION_RPC_HOST") or "127.0.0.1"
    rpc_port: int = int(os.getenv("BGMI_TRANSMISSION_RPC_PORT") or "9091")
    rpc_username: str = os.getenv("BGMI_TRANSMISSION_RPC_USERNAME") or "your_username"
    rpc_password: str = os.getenv("BGMI_TRANSMISSION_RPC_PASSWORD") or "your_password"
    rpc_path: str = os.getenv("BGMI_TRANSMISSION_RPC_PATH") or "/transmission/rpc"


class QBittorrentConfig(BaseSetting):
    rpc_host: str = os.getenv("BGMI_QBITTORRENT_RPC_HOST") or "127.0.0.1"
    rpc_port: int = int(os.getenv("BGMI_QBITTORRENT_RPC_PORT") or "8080")
    rpc_username: str = os.getenv("BGMI_QBITTORRENT_RPC_USERNAME") or "admin"
    rpc_password: str = os.getenv("BGMI_QBITTORRENT_RPC_PASSWORD") or "adminadmin"
    category: str = os.getenv("BGMI_QBITTORRENT_RPC_CATEGORY") or ""


class DelugeConfig(BaseSetting):
    rpc_url: HttpUrl = os.getenv("BGMI_DELUGE_RPC_URL") or "http://127.0.0.1:8112/json"  # type: ignore
    rpc_password: str = os.getenv("BGMI_DELUGE_RPC_PASSWORD") or "deluge"


class HTTP(BaseSetting):
    admin_token: str = Field(
        default_factory=lambda: os.getenv("BGMI_HTTP_ADMIN_TOKEN") or secrets.token_urlsafe(12),
        description="webui admin token",
    )
    danmaku_api_url: str = Field(
        os.getenv("BGMI_HTTP_DANMAKU_API_URL") or "",
        description="danmaku api url, https://github.com/DIYgod/DPlayer#related-projects",
    )
    serve_static_files: bool = Field(
        bool(os.getenv("BGMI_HTTP_SERVE_STATIC_FILES")), description="use tornado serving video files"
    )


class Config(BaseSetting):
    data_source: Source = Field(
        os.getenv("BGMI_DATA_SOURCE") or Source.BangumiMoe, description="data source"
    )  # type: ignore
    download_delegate: str = Field(os.getenv("BGMI_DOWNLOAD_DELEGATE") or "aria2-rpc", description="download delegate")

    tmp_path: Path = Path(os.getenv("BGMI_TMP_PATH") or str(BGMI_PATH.joinpath("tmp")))

    proxy: str = cast(str, os.getenv("BGMI_PROXY") or "")

    @property
    def log_path(self) -> Path:
        return self.tmp_path.joinpath("bgmi.log")

    save_path: Path = Field(
        Path(os.getenv("BGMI_SAVE_PATH") or str(BGMI_PATH.joinpath("bangumi"))), description="bangumi save path"
    )
    front_static_path: Path = Path(os.getenv("BGMI_FRONT_STATIC_PATH") or str(BGMI_PATH.joinpath("front_static")))

    db_path: pathlib.Path = Path(os.getenv("BGMI_DB_PATH") or str(BGMI_PATH.joinpath("bangumi.db")))
    script_path: pathlib.Path = Path(os.getenv("BGMI_SCRIPT_PATH") or str(BGMI_PATH.joinpath("scripts")))
    tools_path: pathlib.Path = Path(os.getenv("BGMI_TOOLS_PATH") or str(BGMI_PATH.joinpath("tools")))

    max_path: int = 3

    bangumi_moe_url: HttpUrl = Field(
        os.getenv("BGMI_BANGUMI_MOE_URL") or "https://bangumi.moe", description="Setting bangumi.moe url"
    )  # type: ignore
    share_dmhy_url: HttpUrl = Field(
        os.getenv("BGMI_SHARE_DMHY_URL") or "https://share.dmhy.org", description="Setting share.dmhy.org url"
    )  # type: ignore
    mikan_url: HttpUrl = Field(
        os.getenv("BGMI_MIKAN_URL") or "https://mikanani.me", description="Setting mikanani.me url"
    )  # type: ignore

    mikan_username: str = os.getenv("BGMI_MIKAN_USERNAME") or ""
    mikan_password: str = os.getenv("BGMI_MIKAN_PASSWORD") or ""

    http: HTTP = HTTP()

    # language
    lang: str = os.getenv("BGMI_LANG") or "zh_cn"

    aria2: Aria2Config = Aria2Config()
    transmission: TransmissionConfig = TransmissionConfig()
    qbittorrent: QBittorrentConfig = QBittorrentConfig()
    deluge: DelugeConfig = DelugeConfig()

    enable_global_include_keywords: bool = False
    global_include_keywords: List[str] = ["1080"]

    enable_global_filters: bool = Field(True, description="enable global filter")
    global_filters: List[str] = Field(
        ["Leopard-Raws", "hevc", "x265", "c-a Raws", "U3-Web"], description="Global exclude keywords"
    )

    save_path_map: Dict[str, Path] = Field(default_factory=dict, description="per-bangumi save path")

    def save(self) -> None:
        s = tomlkit.dumps(json.loads(self.json()))

        CONFIG_FILE_PATH.write_text(s, encoding="utf8")


def pydantic_to_toml(obj: pydantic.BaseModel) -> tomlkit.TOMLDocument:
    doc = tomlkit.document()

    d = obj.dict()

    for name, field in obj.__fields__.items():
        if issubclass(field.type_, BaseModel):
            doc.add(name, pydantic_to_toml(getattr(obj, name)))  # type: ignore
            continue

        value = d[name]

        if isinstance(value, Path):
            item = tomlkit.item(str(value))
        else:
            item = tomlkit.item(value)  # type: ignore

        desc: Optional[str] = field.field_info.description
        if desc:
            item.comment(desc)

        doc.add(name, item)

    return doc


if CONFIG_FILE_PATH.exists():
    try:
        cfg = Config.parse_obj(tomlkit.loads(CONFIG_FILE_PATH.read_text(encoding="utf8")).unwrap())
    except pydantic.ValidationError as e:
        print("配置文件错误，请手动编辑配置文件后重试")
        print("配置文件位置：", CONFIG_FILE_PATH)
        print(e)
        raise SystemExit
else:
    cfg = Config()


def print_config() -> str:
    return tomlkit.dumps(json.loads(cfg.json()))


def write_default_config() -> None:
    if not CONFIG_FILE_PATH.exists():
        doc = pydantic_to_toml(Config())

        CONFIG_FILE_PATH.write_text(tomlkit.dumps(doc))


if __name__ == "__main__":
    Config().save()
