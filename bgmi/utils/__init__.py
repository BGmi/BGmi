import functools
import glob
import gzip
import json
import logging
import os
import re
import struct
import sys
import tarfile
import time
from io import BytesIO
from multiprocessing.pool import ThreadPool
from shutil import move, rmtree
from typing import Any, Callable, List, Optional, Tuple, TypeVar, Union

import requests

from bgmi import __admin_version__, __version__
from bgmi.config import (
    BGMI_PATH,
    DATA_SOURCE,
    ENABLE_GLOBAL_FILTER,
    FRONT_STATIC_PATH,
    GLOBAL_FILTER,
    IS_WINDOWS,
    LOG_PATH,
    SAVE_PATH,
)
from bgmi.lib.constants import SUPPORT_WEBSITE
from bgmi.website.model import Episode

F = TypeVar("F", bound=Callable[..., Any])

log_level = os.environ.get("BGMI_LOG") or "ERROR"
log_level = log_level.upper()
if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
    print("log level error, doing nothing and exit")
    exit(1)
logger = logging.getLogger("BGmi")
try:
    h = logging.FileHandler(LOG_PATH, "a+", "utf-8")
    handlers = [h]
    fs = logging.BASIC_FORMAT
    fmt = logging.Formatter(fs)
    h.setFormatter(fmt)
    logging.root.addHandler(h)
    logging.root.setLevel(log_level)
except OSError:
    logging.basicConfig(stream=sys.stdout, level=logging.getLevelName(log_level))


def log_utils_function(func: F) -> F:
    @functools.wraps(func)
    def echo_func(*func_args, **func_kwargs):  # type: ignore
        logger.debug("")
        logger.debug(f"start function {func.__name__} {func_args} {func_kwargs}")
        r = func(*func_args, **func_kwargs)
        logger.debug(f"return function {func.__name__} {r}")
        logger.debug("")
        return r

    return echo_func  # type: ignore


if (
    IS_WINDOWS
    and "bash" not in os.getenv("SHELL", "").lower()
    and "zsh" not in os.getenv("SHELL", "").lower()
):  # pragma: no cover
    GREEN = ""
    YELLOW = ""
    RED = ""
    COLOR_END = ""
else:
    GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[1;31m"
    COLOR_END = "\033[0m"

color_map = {
    "print_info": "",
    "print_success": GREEN,
    "print_warning": YELLOW,
    "print_error": RED,
}

indicator_map = {
    "print_info": "[*] ",
    "print_success": "[+] ",
    "print_warning": "[-] ",
    "print_error": "[x] ",
}

NPM_REGISTER_DOMAIN = (
    "registry.npmjs.com"
    if os.environ.get("TRAVIS_CI", False)
    else "registry.npm.taobao.org"
)
FRONTEND_NPM_URL = f"https://{NPM_REGISTER_DOMAIN}/bgmi-frontend/"
PACKAGE_JSON_URL = "https://{}/bgmi-frontend/{}".format(
    NPM_REGISTER_DOMAIN, __admin_version__
)


def indicator(f):  # type: ignore
    @functools.wraps(f)
    def wrapper(*args, **kwargs):  # type: ignore
        if kwargs.get("indicator", True):
            func_name = f.__qualname__
            args = (indicator_map.get(func_name, "") + args[0],)
        f(*args, **kwargs)
        sys.stdout.flush()

    return wrapper


def colorize(f):  # type: ignore
    @functools.wraps(f)
    def wrapper(*args, **kwargs):  # type: ignore
        func_name = f.__qualname__
        b, e = (
            color_map.get(func_name, ""),
            COLOR_END if color_map.get(func_name) else "",
        )
        args = tuple(map(lambda s: b + s + e, args))
        return f(*args, **kwargs)

    return wrapper


@indicator
@colorize
def print_info(message: str, indicator: bool = True) -> None:
    logger.info(message)
    print(message + "\n", end="")


@indicator
@colorize
def print_success(message: str, indicator: bool = True) -> None:
    logger.info(message)
    print(message)


@indicator
@colorize
def print_warning(message: str, indicator: bool = True) -> None:
    logger.warning(message)
    print(message)


@indicator
@colorize
def print_error(message: str, exit_: bool = True, indicator: bool = True) -> None:
    logger.error(message)
    print(message)
    if exit_:
        exit(1)


def print_version() -> str:
    return """BGmi {}ver. {}{} built by {}RicterZ{} with ❤️

Github: https://github.com/BGmi/BGmi
Email: ricterzheng@gmail.com
Blog: https://ricterz.me""".format(
        YELLOW, __version__, COLOR_END, YELLOW, COLOR_END
    )


@log_utils_function
def test_connection() -> bool:
    try:
        for website in SUPPORT_WEBSITE:
            if DATA_SOURCE == website["id"]:
                requests.request("head", website["url"], timeout=10)
    except requests.RequestException:
        return False
    return True


def bug_report() -> None:  # pragma: no cover
    print_error(
        "It seems that no bangumi found, if https://bangumi.moe can \n    be opened "
        "normally, please submit issue at: https://github.com/BGmi/BGmi/issues"
    )


_DEFAULT_TERMINAL_WIDTH = 80


@log_utils_function
def get_terminal_col() -> int:  # pragma: no cover
    # https://gist.github.com/jtriley/1108174
    if not IS_WINDOWS:
        import fcntl
        import termios

        try:
            col = struct.unpack(
                "HHHH",
                fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack("HHHH", 0, 0, 0, 0)),
            )[
                1
            ]  # type: int

            return col
        except Exception:
            return _DEFAULT_TERMINAL_WIDTH
    else:
        try:
            from ctypes import (  # type: ignore[attr-defined]
                create_string_buffer,
                windll,
            )

            # stdin handle is -10
            # stdout handle is -11
            # stderr handle is -12
            h = windll.kernel32.GetStdHandle(-12)
            csbi = create_string_buffer(22)
            res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
            if res:
                (
                    bufx,
                    bufy,
                    curx,
                    cury,
                    wattr,
                    left,
                    top,
                    right,
                    bottom,
                    maxx,
                    maxy,
                ) = struct.unpack("hhhhHhhhhhh", csbi.raw)
                sizex = right - left + 1  # type: int
                return sizex
            else:
                import subprocess

                cols = int(subprocess.check_output("tput cols"))
                return cols
        except Exception:
            return _DEFAULT_TERMINAL_WIDTH


@log_utils_function
def check_update(mark: bool = True) -> None:
    def update() -> None:
        try:
            print_info("Checking update ...")
            version = requests.get(
                "https://pypi.python.org/pypi/bgmi/json", verify=False
            ).json()["info"]["version"]

            with open(os.path.join(BGMI_PATH, "latest"), "w") as f:
                f.write(version)

            if version > __version__:
                print_warning(
                    "Please update bgmi to the latest version {}{}{}."
                    "\nThen execute `bgmi upgrade` to migrate database".format(
                        GREEN, version, COLOR_END
                    )
                )
            else:
                print_success("Your BGmi is the latest version.")

            package_json = requests.get(PACKAGE_JSON_URL).json()
            admin_version = package_json["version"]
            if glob.glob(os.path.join(FRONT_STATIC_PATH, "package.json")):
                with open(os.path.join(FRONT_STATIC_PATH, "package.json")) as f:
                    local_version = json.loads(f.read())["version"]
                if [int(x) for x in admin_version.split(".")] > [
                    int(x) for x in local_version.split(".")
                ]:
                    get_web_admin(method="update")
            else:
                print_info(
                    "Use 'bgmi install' to install BGmi frontend / download delegate"
                )
            if not mark:
                update()
                raise SystemExit
        except Exception as e:
            print_warning("Error occurs when checking update, {}".format(str(e)))

    version_file = os.path.join(BGMI_PATH, "version")
    if not os.path.exists(version_file):
        with open(version_file, "w") as f:
            f.write(str(int(time.time())))
        update()

    with open(version_file) as f:
        try:
            data = int(f.read())
            if time.time() - 7 * 24 * 3600 > data:
                with open(version_file, "w") as f:
                    f.write(str(int(time.time())))
                update()
        except ValueError:
            pass


def chinese_to_arabic(cn: str) -> int:
    """
    https://blog.csdn.net/hexrain/article/details/52790126
    :type cn: str
    :rtype: int
    """
    CN_NUM = {
        "〇": 0,
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "零": 0,
        "壹": 1,
        "贰": 2,
        "叁": 3,
        "肆": 4,
        "伍": 5,
        "陆": 6,
        "柒": 7,
        "捌": 8,
        "玖": 9,
        "貮": 2,
        "两": 2,
    }

    CN_UNIT = {
        "十": 10,
        "拾": 10,
        "百": 100,
        "佰": 100,
        "千": 1000,
        "仟": 1000,
        "万": 10000,
        "萬": 10000,
    }
    unit = 0  # current
    ldig = []  # digest
    for cndig in reversed(cn):
        if cndig in CN_UNIT:
            unit = CN_UNIT[cndig]
            if unit == 10000 or unit == 100000000:
                ldig.append(unit)
                unit = 1
        else:
            dig = CN_NUM[cndig]
            if unit:
                dig *= unit
                unit = 0
            ldig.append(dig)
    if unit == 10:
        ldig.append(10)
    val, tmp = 0, 0
    for x in reversed(ldig):
        if x == 10000 or x == 100000000:
            val += tmp * x
            tmp = 0
        else:
            tmp += x
    val += tmp
    return val


FETCH_EPISODE_WITH_BRACKETS = re.compile(r"[【\[]E?(\d+)\s?(?:END)?[】\]]")

FETCH_EPISODE_ZH = re.compile(r"第?\s?(\d{1,3})\s?[話话集]")
FETCH_EPISODE_ALL_ZH = re.compile(r"第([^第]*?)[話话集]")
FETCH_EPISODE_ONLY_NUM = re.compile(r"^([\d]{2,})$")

FETCH_EPISODE_RANGE = re.compile(r"[^sS][\d]{2,}\s?-\s?([\d]{2,})")
FETCH_EPISODE_RANGE_ZH = re.compile(r"[第][\d]{2,}\s?-\s?([\d]{2,})\s?[話话集]")
FETCH_EPISODE_RANGE_ALL_ZH = re.compile(r"[全]([^-^第]*?)[話话集]")

FETCH_EPISODE_OVA_OAD = re.compile(r"([\d]{2,})\s?\((?:OVA|OAD)\)]")
FETCH_EPISODE_WITH_VERSION = re.compile(r"[【\[](\d+)\s? *v\d(?:END)?[】\]]")

FETCH_EPISODE = (
    FETCH_EPISODE_ZH,
    FETCH_EPISODE_ALL_ZH,
    FETCH_EPISODE_WITH_BRACKETS,
    FETCH_EPISODE_ONLY_NUM,
    FETCH_EPISODE_RANGE,
    FETCH_EPISODE_RANGE_ALL_ZH,
    FETCH_EPISODE_OVA_OAD,
    FETCH_EPISODE_WITH_VERSION,
)


@log_utils_function
def parse_episode(episode_title: str) -> int:
    """
    parse episode from title
    :param episode_title: episode title
    :type episode_title: str
    :return: episode of this title
    :rtype: int
    """
    spare = None

    def get_real_episode(episode_list: List[Union[str, int]]) -> int:
        return min(int(x) for x in episode_list)

    _ = FETCH_EPISODE_RANGE_ALL_ZH.findall(episode_title)
    if _ and _[0]:
        logger.debug("return episode range all zh")
        return int(0)

    _ = FETCH_EPISODE_RANGE.findall(episode_title)
    if _ and _[0]:
        logger.debug("return episode range")
        return int(0)

    _ = FETCH_EPISODE_RANGE_ZH.findall(episode_title)
    if _ and _[0]:
        logger.debug("return episode range zh")
        return int(0)

    _ = FETCH_EPISODE_ZH.findall(episode_title)
    if _ and _[0].isdigit():
        logger.debug("return episode zh")
        return int(_[0])

    _ = FETCH_EPISODE_ALL_ZH.findall(episode_title)
    if _ and _[0]:
        try:
            logger.debug("try return episode all zh %s", _)
            e = chinese_to_arabic(_[0])
            logger.debug("return episode all zh")
            return e
        except Exception:
            logger.debug("can't convert %s to int", _[0])

    _ = FETCH_EPISODE_WITH_VERSION.findall(episode_title)
    if _ and _[0].isdigit():
        logger.debug("return episode range with version")
        return int(_[0])

    _ = FETCH_EPISODE_WITH_BRACKETS.findall(episode_title)
    if _:
        logger.debug("return episode with brackets")
        return get_real_episode(_)

    logger.debug("don't match any regex, try match after split")
    for i in episode_title.replace("[", " ").replace("【", ",").split(" "):
        for regexp in FETCH_EPISODE:
            match = regexp.findall(i)
            if match and match[0].isdigit():
                m = int(match[0])
                if m > 1000:
                    spare = m
                else:
                    logger.debug(f"match {i} {regexp} {m}")
                    return m

    if spare:
        return spare

    return 0


@log_utils_function
def normalize_path(url: str) -> str:
    """
    normalize link to path

    :param url: path or url to normalize
    :type url: str
    :return: normalized path
    :rtype: str
    """
    url = url.replace("http://", "http/").replace("https://", "https/")
    illegal_char = [":", "*", "?", '"', "<", ">", "|", "'"]
    for char in illegal_char:
        url = url.replace(char, "")

    if url.startswith("/"):
        return url[1:]
    else:
        return url


def get_web_admin(method: str) -> None:
    print_info("{}ing BGmi frontend".format(method[0].upper() + method[1:]))

    try:
        r = requests.get(FRONTEND_NPM_URL).json()
        version = requests.get(PACKAGE_JSON_URL).json()
        if (
            "error" in version and version["reason"] == "document not found"
        ):  # pragma: no cover
            print_error(
                "Cnpm has not synchronized the latest version of BGmi-frontend from npm,"
                " please try it later"
            )
            return
        tar_url = r["versions"][version["version"]]["dist"]["tarball"]
        r = requests.get(tar_url)
    except requests.exceptions.ConnectionError:
        print_warning("failed to download web admin")
        return
    except json.JSONDecodeError:
        print_warning("failed to download web admin")
        return
    admin_zip = BytesIO(r.content)
    with gzip.GzipFile(fileobj=admin_zip) as f:
        tar_file = BytesIO(f.read())

    rmtree(FRONT_STATIC_PATH)
    os.makedirs(FRONT_STATIC_PATH)

    with tarfile.open(fileobj=tar_file) as tar_file_obj:
        tar_file_obj.extractall(path=FRONT_STATIC_PATH)

    for file in os.listdir(os.path.join(FRONT_STATIC_PATH, "package", "dist")):
        move(
            os.path.join(FRONT_STATIC_PATH, "package", "dist", file),
            os.path.join(FRONT_STATIC_PATH, file),
        )
    with open(os.path.join(FRONT_STATIC_PATH, "package.json"), "w+") as pkg:
        pkg.write(json.dumps(version))
    print_success(
        "Web admin page {} successfully. version: {}".format(method, version["version"])
    )


@log_utils_function
def convert_cover_url_to_path(cover_url: str) -> Tuple[str, str]:
    """
    convert bangumi cover to file path

    :param cover_url: bangumi cover path
    :type cover_url:str
    :rtype: str,str
    :return: dir_path, file_path
    """

    cover_url = normalize_path(cover_url)
    file_path = os.path.join(SAVE_PATH, "cover")
    file_path = os.path.join(file_path, cover_url)
    dir_path = os.path.dirname(file_path)

    return dir_path, file_path


@log_utils_function
def download_file(url: str) -> Optional[requests.Response]:
    if url.startswith("https://") or url.startswith("http://"):
        print_info(f"Download: {url}")
        return requests.get(url)
    return None


@log_utils_function
def download_cover(cover_url_list: List[str]) -> None:
    p = ThreadPool(4)
    content_list = p.map(download_file, cover_url_list)
    p.close()
    for index, r in enumerate(content_list):
        if not r:
            continue

        dir_path, file_path = convert_cover_url_to_path(cover_url_list[index])
        if not glob.glob(dir_path):
            os.makedirs(dir_path)
        with open(file_path, "wb") as f:
            f.write(r.content)


def episode_filter_regex(data: List[Episode], regex: str = None) -> List[Episode]:
    """

    :param data: list of bangumi dict
    :param regex: regex
    """
    if regex:
        try:
            match = re.compile(regex)
            data = [s for s in data if match.findall(s.title)]
        except re.error as e:
            if os.getenv("DEBUG"):  # pragma: no cover
                import traceback

                traceback.print_exc()
                raise e
            return data

    if not ENABLE_GLOBAL_FILTER == "0":
        data = list(
            filter(
                lambda s: all(
                    map(
                        lambda t: t.strip().lower() not in s.title.lower(),
                        GLOBAL_FILTER.split(","),
                    )
                ),
                data,
            )
        )

    return data
