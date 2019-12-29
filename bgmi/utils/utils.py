import gzip
import json
import os
import struct
import subprocess
import tarfile
from io import BytesIO
from shutil import move, rmtree
from typing import Tuple

import requests

from bgmi import config
from bgmi.logger import logger
from bgmi.utils.pure_utils import normalize_path, parallel

from ._decorator import _indicator, colorize, disable_in_test, log_utils_function


@disable_in_test
@_indicator
@colorize
def print_info(message, indicator=True):
    logger.info(message)


@disable_in_test
@_indicator
@colorize
def print_success(message, indicator=True):
    logger.info(message)


@disable_in_test
@_indicator
@colorize
def print_warning(message, indicator=True):
    logger.warning(message)


@disable_in_test
@_indicator
@colorize
def print_error(message, exit_: bool = True, indicator=True):
    logger.error(message)

    if exit_:
        exit(1)


def bug_report():  # pragma: no cover
    print_error(
        'It seems that no bangumi found, if https://bangumi.moe can \n'
        '    be opened normally, '
        'please submit issue at: https://github.com/BGmi/BGmi/issues',
        exit_=True
    )


@log_utils_function
def get_terminal_col():  # pragma: no cover
    if 'SYSTEM_TEAMFOUNDATIONSERVERURI' in os.environ:
        # azure pipelines
        return 80

    # https://gist.github.com/jtriley/1108174
    if not config.config_obj.IS_WINDOWS:
        import fcntl
        import termios

        _, col, _, _ = struct.unpack(
            'HHHH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0))
        )

        return col
    try:
        from ctypes import windll, create_string_buffer

        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12
        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (_, _, _, _, _, left, _, right, _, _, _) = struct.unpack('hhhhHhhhhhh', csbi.raw)
            sizex = right - left + 1
            # sizey = bottom - top + 1
            return sizex
        cols = int(subprocess.check_output('tput cols'))
        return cols
    except BaseException:
        return 80


def unzip_zipped_file(file_content, front_version):
    admin_zip = BytesIO(file_content)
    with gzip.GzipFile(fileobj=admin_zip) as f:
        tar_file = BytesIO(f.read())

    rmtree(config.config_obj.FRONT_STATIC_PATH)
    os.makedirs(config.config_obj.FRONT_STATIC_PATH)

    with tarfile.open(fileobj=tar_file) as tar_file_obj:
        tar_file_obj.extractall(path=config.config_obj.FRONT_STATIC_PATH)

    for file in os.listdir(os.path.join(config.config_obj.FRONT_STATIC_PATH, 'package', 'dist')):
        move(
            os.path.join(config.config_obj.FRONT_STATIC_PATH, 'package', 'dist', file),
            os.path.join(config.config_obj.FRONT_STATIC_PATH, file)
        )
    with open(os.path.join(config.config_obj.FRONT_STATIC_PATH, 'package.json'), 'w+') as f:
        f.write(json.dumps(front_version))


@log_utils_function
def convert_cover_url_to_path(cover_url: str,
                              save_path=config.config_obj.SAVE_PATH) -> Tuple[str, str]:
    """
    convert bangumi cover to file path


    Parameters
    ----------
        cover_url: cover uri
        save_path: root of save path
    """

    cover_url = normalize_path(cover_url)
    file_path = os.path.join(save_path, 'cover')
    file_path = os.path.join(file_path, cover_url)
    dir_path = os.path.dirname(file_path)

    return dir_path, file_path


@log_utils_function
def download_file(url):
    if url.startswith('https://') or url.startswith('http://'):
        print_info(f'Download: {url}')
        r = requests.get(url)

        _, file_path = convert_cover_url_to_path(url)

        with open(file_path, 'wb') as f:
            f.write(r.content)


@log_utils_function
def download_cover(cover_url_list):
    """

    :param cover_url_list:
    :type cover_url_list: list
    :return:
    """
    for url in cover_url_list:
        dir_path, _ = convert_cover_url_to_path(url)

        if os.path.exists(dir_path):
            if not os.path.isdir(dir_path):
                os.remove(dir_path)

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    parallel(download_file, cover_url_list)
