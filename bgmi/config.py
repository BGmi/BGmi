import configparser
import hashlib
import os
import platform
import random
import tempfile
from typing import Any, Dict, Optional

# download delegate
__wget__ = ("WGET_PATH",)
__thunder__ = ("XUNLEI_LX_PATH",)
__transmission__ = (
    "TRANSMISSION_RPC_URL",
    "TRANSMISSION_RPC_PORT",
    "TRANSMISSION_RPC_USERNAME",
    "TRANSMISSION_RPC_PASSWORD",
)
__qbittorrent__ = (
    "QBITTORRENT_HOST",
    "QBITTORRENT_PORT",
    "QBITTORRENT_USERNAME",
    "QBITTORRENT_PASSWORD",
    "QBITTORRENT_CATEGORY",
)
__aria2__ = (
    "ARIA2_RPC_URL",
    "ARIA2_RPC_TOKEN",
)
__deluge__ = ("DELUGE_RPC_URL", "DELUGE_RPC_PASSWORD")

__download_delegate__ = (
    __wget__ + __thunder__ + __aria2__ + __transmission__ + __deluge__ + __qbittorrent__
)

# fake __all__
__all__ = (
    "BANGUMI_MOE_URL",
    "SAVE_PATH",
    "DOWNLOAD_DELEGATE",
    "MAX_PAGE",
    "DATA_SOURCE",
    "TMP_PATH",
    "DANMAKU_API_URL",
    "LANG",
    "FRONT_STATIC_PATH",
    "ADMIN_TOKEN",
    "SHARE_DMHY_URL",
    "GLOBAL_FILTER",
    "ENABLE_GLOBAL_FILTER",
    "TORNADO_SERVE_STATIC_FILES",
)

# cannot be rewrite
__readonly__ = (
    "BGMI_PATH",
    "DB_PATH",
    "CONFIG_FILE_PATH",
    "TOOLS_PATH",
    "SCRIPT_PATH",
    "SCRIPT_DB_PATH",
    "FRONT_STATIC_PATH",
)

# writeable
__writeable__ = tuple(i for i in __all__ if i not in __readonly__)

# the real __all__
__all__ = __all__ + __download_delegate__ + __readonly__  # type: ignore


DOWNLOAD_DELEGATE_MAP = {
    "rr!": __wget__,
    "aria2-rpc": __aria2__,
    "xunlei": __thunder__,
    "transmission-rpc": __transmission__,
    "deluge-rpc": __deluge__,
    "qbittorrent-webapi": __qbittorrent__,
}

if not os.environ.get("BGMI_PATH"):  # pragma: no cover
    if platform.system() == "Windows":
        BGMI_PATH = os.path.join(
            os.environ.get("USERPROFILE", tempfile.gettempdir()), ".bgmi"
        )
        if not BGMI_PATH:
            raise SystemExit
    else:
        BGMI_PATH = os.path.join(os.environ.get("HOME", "/tmp"), ".bgmi")
else:
    BGMI_PATH = os.environ["BGMI_PATH"]

DB_PATH = os.path.join(BGMI_PATH, "bangumi.db")
CONFIG_FILE_PATH = os.path.join(BGMI_PATH, "bgmi.cfg")

SCRIPT_DB_PATH = os.path.join(BGMI_PATH, "script.db")
SCRIPT_PATH = os.path.join(BGMI_PATH, "scripts")
TOOLS_PATH = os.path.join(BGMI_PATH, "tools")


def read_config() -> None:
    c = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE_PATH):
        write_default_config()
        return
    c.read(CONFIG_FILE_PATH, encoding="utf-8")

    for i in __writeable__:
        if c.has_option("bgmi", i):
            v: Any = c.get("bgmi", i)
            if i == "MAX_PAGE":
                v = int(v)
            globals().update({i: v})

    for i in DOWNLOAD_DELEGATE_MAP.get(DOWNLOAD_DELEGATE, []):
        if c.has_option(DOWNLOAD_DELEGATE, i):
            globals().update({i: c.get(DOWNLOAD_DELEGATE, i)})


def print_config() -> Optional[str]:
    c = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE_PATH):
        return None

    c.read(CONFIG_FILE_PATH, encoding="utf-8")
    string = ""
    string += "[bgmi]\n"
    for i in __writeable__:
        string += "{}={}\n".format(i, c.get("bgmi", i))

    string += f"\n[{DOWNLOAD_DELEGATE}]\n"
    for i in DOWNLOAD_DELEGATE_MAP.get(DOWNLOAD_DELEGATE, []):
        string += "{}={}\n".format(i, c.get(DOWNLOAD_DELEGATE, i))
    return string


def write_default_config() -> None:
    c = configparser.ConfigParser()
    if not c.has_section("bgmi"):
        c.add_section("bgmi")

    for k in __writeable__:
        v = globals().get(k, "0")
        if k == "ADMIN_TOKEN" and v is None:
            v = hashlib.md5(str(random.random()).encode("utf-8")).hexdigest()

        c.set("bgmi", k, str(v))

    if DOWNLOAD_DELEGATE not in DOWNLOAD_DELEGATE_MAP.keys():
        raise Exception(DOWNLOAD_DELEGATE)

    if not c.has_section(DOWNLOAD_DELEGATE):
        c.add_section(DOWNLOAD_DELEGATE)

    for k in DOWNLOAD_DELEGATE_MAP.get(DOWNLOAD_DELEGATE, []):
        v = globals().get(k, None)
        c.set(DOWNLOAD_DELEGATE, k, v)

    try:
        with open(CONFIG_FILE_PATH, "w+", encoding="utf-8") as f:
            c.write(f)
    except OSError:
        print("[-] Error writing to config file and ignored")


def write_config(
    config: Optional[str] = None, value: Optional[str] = None
) -> Dict[str, Any]:
    if not os.path.exists(CONFIG_FILE_PATH):
        write_default_config()
        return {
            "status": "error",
            "message": "Config file does not exists, writing default config file",
            "data": [],
        }

    c = configparser.ConfigParser()
    c.read(CONFIG_FILE_PATH, encoding="utf-8")
    result = {}  # type: Dict[str, Any]
    try:
        if config is None:
            result = {"status": "info", "message": print_config()}

        elif value is None:  # config(config, None)
            result = {"status": "info"}

            if config in __download_delegate__:
                result["message"] = "{}={}".format(
                    config, c.get(DOWNLOAD_DELEGATE, config)
                )
            else:
                result["message"] = "{}={}".format(config, c.get("bgmi", config))

        else:  # config(config, Value)
            if config in __writeable__:
                if config == "DOWNLOAD_DELEGATE" and value not in DOWNLOAD_DELEGATE_MAP:
                    result = {
                        "status": "error",
                        "message": "{} is not a support download_delegate".format(
                            value
                        ),
                    }
                else:
                    c.set("bgmi", config, value)
                    with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                        c.write(f)

                    read_config()
                    if config == "DOWNLOAD_DELEGATE":
                        if not c.has_section(DOWNLOAD_DELEGATE):
                            c.add_section(DOWNLOAD_DELEGATE)
                            for i in DOWNLOAD_DELEGATE_MAP[DOWNLOAD_DELEGATE]:
                                v = globals().get(i, "")
                                c.set(DOWNLOAD_DELEGATE, i, v)

                            with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                                c.write(f)

                    result = {
                        "status": "success",
                        "message": f"{config} has been set to {value}",
                    }

            elif config in DOWNLOAD_DELEGATE_MAP.get(DOWNLOAD_DELEGATE, []):
                c.set(DOWNLOAD_DELEGATE, config, value)
                with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                    c.write(f)

                result = {
                    "status": "success",
                    "message": f"{config} has been set to {value}",
                }
            else:
                result = {
                    "status": "error",
                    "message": f"{config} does not exist or not writeable",
                }

    except configparser.NoOptionError:
        write_default_config()
        result = {
            "status": "error",
            "message": "Error in config file, try rerun `bgmi config`",
        }

    result["data"] = [
        {"writable": True, "name": x, "value": globals()[x]} for x in __writeable__
    ] + [{"writable": False, "name": x, "value": globals()[x]} for x in __readonly__]
    return result


# --------- Writeable ---------- #
# Setting bangumi.moe url
BANGUMI_MOE_URL = "https://bangumi.moe"

# Setting share.dmhy.org url
SHARE_DMHY_URL = "https://share.dmhy.org"

# Setting bangumi.moe url
DATA_SOURCE = "bangumi_moe"

# BGmi user path
SAVE_PATH = os.path.join(BGMI_PATH, "bangumi")
FRONT_STATIC_PATH = os.path.join(BGMI_PATH, "front_static")

# admin token
ADMIN_TOKEN = None

# Xunlei offline download
XUNLEI_LX_PATH = os.path.join(BGMI_PATH, "bgmi-lx")

# temp path
TMP_PATH = os.path.join(BGMI_PATH, "tmp")

# log path
LOG_PATH = os.path.join(TMP_PATH, "bgmi.log")

# Download delegate
DOWNLOAD_DELEGATE = "aria2-rpc"

# danmaku api url, https://github.com/DIYgod/DPlayer#related-projects
DANMAKU_API_URL = ""

# language
LANG = "zh_cn"

# max page
MAX_PAGE = 3

# aria2
ARIA2_RPC_URL = "http://localhost:6800/rpc"
ARIA2_RPC_TOKEN = "token:"

# deluge
DELUGE_RPC_URL = "http://127.0.0.1:8112/json"
DELUGE_RPC_PASSWORD = "deluge"

# path of wget
WGET_PATH = "/usr/bin/wget"

# transmission-rpc
TRANSMISSION_RPC_URL = "127.0.0.1"
TRANSMISSION_RPC_PORT = "9091"
TRANSMISSION_RPC_USERNAME = "your_username"
TRANSMISSION_RPC_PASSWORD = "your_password"

# qbittorrent-webapi
QBITTORRENT_HOST = "127.0.0.1"
QBITTORRENT_PORT = "8080"
QBITTORRENT_USERNAME = "admin"
QBITTORRENT_PASSWORD = "adminadmin"
QBITTORRENT_CATEGORY = ""

# tag of bangumi on bangumi.moe
BANGUMI_TAG = "549ef207fe682f7549f1ea90"

# Global blocked keyword
GLOBAL_FILTER = "Leopard-Raws, hevc, x265, c-a Raws, U3-Web"

# enable global filter
ENABLE_GLOBAL_FILTER = "1"

# use tornado serving video files
TORNADO_SERVE_STATIC_FILES = "0"

# ------------------------------ #
# !!! Read config from file and write to globals() !!!
read_config()
# ------------------------------ #
# will be used in other other models
__all_writable_now__ = __writeable__ + DOWNLOAD_DELEGATE_MAP[DOWNLOAD_DELEGATE]

# --------- Read-Only ---------- #
# platform
IS_WINDOWS = platform.system() == "Windows"


if __name__ == "__main__":
    write_default_config()
