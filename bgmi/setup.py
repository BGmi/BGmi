import os
from pathlib import Path
from shutil import copy
from typing import List

from bgmi.config import BGMI_PATH, IS_WINDOWS, cfg
from bgmi.lib.table import Base, engine
from bgmi.utils import print_error, print_info, print_success


def install_crontab() -> None:
    print_info("Installing crontab job")
    if IS_WINDOWS:
        copy(os.path.join(os.path.dirname(__file__), "others/cron.vbs"), BGMI_PATH)
        os.system(
            'schtasks /Create /SC HOURLY /TN "bgmi updater" /TR "{}"  /IT /F'.format(
                os.path.join(BGMI_PATH, "cron.vbs")
            )
        )
    else:
        path = os.path.join(os.path.dirname(__file__), "others/crontab.sh")
        os.system(f"bash '{path}'")


def create_dir() -> None:
    path_to_create: List[Path] = [
        BGMI_PATH,
        cfg.save_path,
        cfg.tmp_path,
        cfg.script_path,
        cfg.tools_path,
        cfg.front_static_path,
    ]

    # bgmi home dir
    try:
        for path in path_to_create:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                print_success(f"{path} created successfully")
    except OSError as e:
        print_error(f"Error: {str(e)}")


def init_db() -> None:
    Base.metadata.create_all(engine, checkfirst=True)
