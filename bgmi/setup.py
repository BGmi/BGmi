import os
import subprocess
import sys
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
        output = subprocess.getoutput("crontab -l")

        extra = []
        for line in output.splitlines():
            if "bgmi update" in line:
                continue
            if "bgmi cal" in line:
                continue

            extra.append(line)

        extra.append(f"10 */2 * * * LC_ALL=en_US.UTF-8 {sys.executable} -m bgmi update")
        extra.append(f"0 */12 * * * LC_ALL=en_US.UTF-8 {sys.executable} -m bgmi cal --force-update --download-cover")

        with subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE) as p:
            for line in extra:
                p.stdin.write(f"{line}\n".encode())  # type: ignore


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
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                print_success(f"{path} created successfully")
    except OSError as e:
        print_error(f"Error: {str(e)}")


def init_db() -> None:
    Base.metadata.create_all(engine, checkfirst=True)
