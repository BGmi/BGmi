import json
import os
import pathlib
import platform
import secrets
import tempfile
from pathlib import Path
from typing import Annotated, Dict, List, Optional, cast

import pydantic
import tomlkit
from pydantic import AnyUrl, BaseModel, ConfigDict, Field, HttpUrl

try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum  # type: ignore


class Source(StrEnum):
    Mikan = "mikan_project"
    BangumiMoe = "bangumi_moe"
    Dmhy = "dmhy"


IS_WINDOWS = platform.system() == "Windows"


def get_bgmi_home() -> Path:
    h = os.environ.get("BGMI_PATH")

    if h:
        return Path(h)

    if IS_WINDOWS:
        home_dir = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    else:
        home_dir = os.environ.get("HOME")

    if home_dir:
        return Path(home_dir).joinpath(".bgmi")

    tmp_dir = Path(tempfile.gettempdir()).joinpath(".bgmi")
    print(f"can't find user home, use temp dir {tmp_dir} as bgmi home")
    return tmp_dir


BGMI_PATH = get_bgmi_home().absolute()

CONFIG_FILE_PATH = BGMI_PATH / "config.toml"


class BaseSetting(BaseModel):
    model_config = ConfigDict(extra="allow", validate_assignment=True)


class Aria2Config(BaseSetting):
    rpc_url: str = os.getenv("BGMI_ARIA2_RPC_URL") or "http://127.0.0.1:6800/rpc"
    rpc_token: str = os.getenv("BGMI_ARIA2_RPC_TOKEN") or "token:"


class TransmissionConfig(BaseSetting):
    rpc_host: str = os.getenv("BGMI_TRANSMISSION_RPC_HOST") or "127.0.0.1"
    rpc_port: int = int(os.getenv("BGMI_TRANSMISSION_RPC_PORT") or "9091")
    rpc_username: str = os.getenv("BGMI_TRANSMISSION_RPC_USERNAME") or "your_username"
    rpc_password: str = os.getenv("BGMI_TRANSMISSION_RPC_PASSWORD") or "your_password"
    rpc_path: str = os.getenv("BGMI_TRANSMISSION_RPC_PATH") or "/transmission/rpc"
    labels: Annotated[Optional[List[str]], pydantic.Field(["bgmi"])] = None


class QBittorrentConfig(BaseSetting):
    rpc_host: str = os.getenv("BGMI_QBITTORRENT_RPC_HOST") or "127.0.0.1"
    rpc_port: int = int(os.getenv("BGMI_QBITTORRENT_RPC_PORT") or "8080")
    rpc_username: str = os.getenv("BGMI_QBITTORRENT_RPC_USERNAME") or "admin"
    rpc_password: str = os.getenv("BGMI_QBITTORRENT_RPC_PASSWORD") or "adminadmin"
    category: str = os.getenv("BGMI_QBITTORRENT_RPC_CATEGORY") or ""
    tags: Optional[List[str]] = pydantic.Field(["bgmi"])


class DelugeConfig(BaseSetting):
    rpc_url: HttpUrl = Field(
        os.getenv("BGMI_DELUGE_RPC_URL") or "http://127.0.0.1:8112/json", validate_default=True
    )  # type: ignore
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
        cast(bool, os.getenv("BGMI_HTTP_SERVE_STATIC_FILES") or False),
        description="serve static files with main",
        validate_default=True,
    )


class Config(BaseSetting):
    data_source: Source = Field(
        os.getenv("BGMI_DATA_SOURCE") or Source.BangumiMoe, description="data source"
    )  # type: ignore
    download_delegate: str = Field(os.getenv("BGMI_DOWNLOAD_DELEGATE") or "aria2-rpc", description="download delegate")

    tmp_path: Path = Field(Path(os.getenv("BGMI_TMP_PATH") or BGMI_PATH.joinpath("tmp")), validate_default=True)

    proxy: str = cast(str, os.getenv("BGMI_PROXY") or "")

    @property
    def log_path(self) -> Path:
        return self.tmp_path.joinpath("bgmi.log")

    save_path: Path = Field(
        Path(os.getenv("BGMI_SAVE_PATH") or str(BGMI_PATH.joinpath("bangumi"))),
        description="bangumi save path",
        validate_default=True,
    )
    front_static_path: Path = Field(
        Path(os.getenv("BGMI_FRONT_STATIC_PATH") or str(BGMI_PATH.joinpath("front_static"))), validate_default=True
    )

    db_path: pathlib.Path = Field(
        Path(os.getenv("BGMI_DB_PATH") or str(BGMI_PATH.joinpath("bangumi.db"))), validate_default=True
    )
    script_path: pathlib.Path = Field(
        Path(os.getenv("BGMI_SCRIPT_PATH") or str(BGMI_PATH.joinpath("scripts"))), validate_default=True
    )
    tools_path: pathlib.Path = Field(
        Path(os.getenv("BGMI_TOOLS_PATH") or str(BGMI_PATH.joinpath("tools"))), validate_default=True
    )

    max_path: int = 3

    bangumi_moe_url: HttpUrl = Field(
        HttpUrl(os.getenv("BGMI_BANGUMI_MOE_URL") or "https://bangumi.moe"),
        description="Setting bangumi.moe url",
        validate_default=True,
    )  # type: ignore
    share_dmhy_url: HttpUrl = Field(
        HttpUrl(os.getenv("BGMI_SHARE_DMHY_URL") or "https://share.dmhy.org"),
        description="Setting share.dmhy.org url",
        validate_default=True,
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
    global_include_keywords: List[str] = Field(["1080"])

    enable_global_filters: bool = Field(True, description="enable global filter")
    global_filters: List[str] = Field(
        ["Leopard-Raws", "hevc", "x265", "c-a Raws", "U3-Web"], description="Global exclude keywords"
    )

    save_path_map: Dict[str, Path] = Field(default_factory=dict, description="per-bangumi save path")

    def save(self) -> None:
        s = tomlkit.dumps(json.loads(self.model_dump_json()))

        CONFIG_FILE_PATH.write_text(s, encoding="utf8")


def pydantic_to_toml(obj: pydantic.BaseModel) -> tomlkit.TOMLDocument:
    doc = tomlkit.document()

    d = obj.model_dump()

    for name, field in obj.model_fields.items():
        if field.annotation is None:
            continue

        if isinstance(field.annotation, type) and issubclass(field.annotation, BaseModel):
            value = getattr(obj, name)
            if value is None:
                continue
            doc.add(name, pydantic_to_toml(value))  # type: ignore
            continue

        value = d[name]

        if isinstance(value, (Path, AnyUrl)):
            item = tomlkit.item(str(value))
        elif value is None:
            continue
        else:
            item = tomlkit.item(value)  # type: ignore

        desc: Optional[str] = field.description
        if desc:
            item.comment(desc)

        doc.add(name, item)

    return doc


if CONFIG_FILE_PATH.exists():
    try:
        cfg = Config.model_validate(tomlkit.loads(CONFIG_FILE_PATH.read_text(encoding="utf8")).unwrap())
    except pydantic.ValidationError as e:
        print("配置文件错误，请手动编辑配置文件后重试")
        print("配置文件位置：", CONFIG_FILE_PATH)
        print(e)
        raise SystemExit from e
else:
    cfg = Config()


def print_config() -> str:
    return tomlkit.dumps(json.loads(cfg.model_dump_json()))


def write_default_config() -> None:
    if not CONFIG_FILE_PATH.exists():
        doc = pydantic_to_toml(Config())

        CONFIG_FILE_PATH.write_text(tomlkit.dumps(doc))


if __name__ == "__main__":
    pydantic_to_toml(Config())
