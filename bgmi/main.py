import argparse
import os
import sys
from typing import List, Optional

from loguru import logger

from bgmi.config import BGMI_PATH, cfg, write_default_config
from bgmi.lib.cli import controllers
from bgmi.lib.constants import ACTION_COMPLETE, actions_and_arguments
from bgmi.lib.update import update_database
from bgmi.setup import create_dir, init_db, install_crontab
from bgmi.utils import check_update, get_web_admin, print_version, print_warning


# main function
def main(argv: Optional[List[str]] = None) -> None:
    setup()
    c = argparse.ArgumentParser()

    c.add_argument(
        "--version",
        help="Show the version of BGmi.",
        action="version",
        version=print_version(),
    )

    sub_parser = c.add_subparsers(help="BGmi actions", dest="action")

    for action in actions_and_arguments:
        tmp_sub_parser = sub_parser.add_parser(action["action"], help=action.get("help", ""))
        for sub_action in action.get("arguments", []):
            if isinstance(sub_action["dest"], str):
                tmp_sub_parser.add_argument(sub_action["dest"], **sub_action["kwargs"])
            if isinstance(sub_action["dest"], list):
                tmp_sub_parser.add_argument(*sub_action["dest"], **sub_action["kwargs"])

    sub_parser.add_parser(
        ACTION_COMPLETE,
        help='Gen completion, `eval "$(bgmi complete)"` ' 'or `eval "$(bgmi complete|dos2unix)"`',
    )

    ret = c.parse_args(argv)
    if ret.action == "install":
        get_web_admin(method="install")
    elif ret.action == "upgrade":
        create_dir()
        update_database()
        check_update()
    else:
        check_update()
        controllers(ret)


def setup() -> None:
    logger.remove()
    logger.add(
        sys.stderr, format="<blue>{time:YYYY-MM-DD HH:mm:ss}</blue> {level:7} | <level>{message}</level>", level="INFO"
    )
    logger.add(cfg.log_path.parent.joinpath("{time:YYYY-MM-DD}.log"), format="{time} {level} {message}", level="INFO")
    need_to_init = False
    if not os.path.exists(BGMI_PATH):
        need_to_init = True
        print_warning(f"BGMI_PATH {BGMI_PATH} does not exist, installing")

    create_dir()
    init_db()
    if need_to_init:
        install_crontab()
    write_default_config()


if __name__ == "__main__":
    setup()
    main()
