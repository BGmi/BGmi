import os
import sys
from typing import Any

import click as click
from loguru import logger

from bgmi import __version__
from bgmi.config import BGMI_PATH, CONFIG_FILE_PATH, cfg, print_config, write_default_config
from bgmi.lib import controllers as ctl
from bgmi.lib.constants import ACTION_COMPLETE, SUPPORT_WEBSITE
from bgmi.lib.download import download_prepare
from bgmi.lib.update import update_database
from bgmi.setup import create_dir, init_db, install_crontab
from bgmi.utils import check_update, get_web_admin, print_version, print_warning


@click.group()
@click.version_option(__version__, prog_name="bgmi", message=print_version())
@click.pass_context
def cli(ctx: click.Context):
    logger.remove()
    logger.add(
        sys.stderr, format="<blue>{time:YYYY-MM-DD HH:mm:ss}</blue> {level:7} | <level>{message}</level>", level="INFO"
    )
    logger.add(cfg.log_path.parent.joinpath("{time:YYYY-MM-DD}.log"), format="{time} {level} {message}", level="INFO")

    if ctx.command not in ["install", "upgrade", ACTION_COMPLETE]:
        check_update()


@cli.command()
def install():
    get_web_admin(method="install")
    need_to_init = False
    if not os.path.exists(BGMI_PATH):
        need_to_init = True
        print_warning(f"BGMI_PATH {BGMI_PATH} does not exist, installing")

    create_dir()
    init_db()
    if need_to_init:
        install_crontab()

    write_default_config()


@cli.command()
def upgrade():
    create_dir()
    update_database()
    check_update()


def config_wrapper(ret: Any) -> None:
    name = ret.name
    value = ret.value

    if name or value:
        print("use config command to change config has been removed, please edit config file directly")
        print(f"config file location: {str(CONFIG_FILE_PATH)!r}")
    else:
        print(print_config())


@cli.command()
@click.argument("bangumi_source", required=True, type=click.Choice([x["id"] for x in SUPPORT_WEBSITE]))
def source(bangumi_source: str) -> None:
    result = ctl.source(data_source=bangumi_source)
    globals()["print_{}".format(result["status"])](result["message"])


@cli.command()
def config():
    print(print_config())


@cli.command(help="Search torrents from data source by keyword")
@click.argument("keyword")
@click.option("--count", type=int, help="The max page count of search result.")
@click.option("--regex-filter", "regex", help="Regular expression filter of title.")
@click.option("--download", is_flag=True, show_default=True, default=False, type=bool, help="Download search result.")
@click.option("--dupe", is_flag=True, show_default=True, default=False, type=bool, help="Show duplicated episode")
@click.option("--min-episode", "min_episode", type=int, help="Minimum episode filter of title.")
@click.option("--max-episode", "max_episode", type=int, help="Maximum episode filter of title.")
@click.option(
    "--tag", is_flag=True, show_default=True, default=False, help="Use tag to search (if data source supported)."
)
@click.option("--subtitle", help="Subtitle group filter of title (Need --tag enabled)")
def search(
    keyword: str,
    count: int,
    regex: str,
    download: bool,
    dupe: bool,
    min_episode: int,
    max_episode: int,
    tag: bool,
    subtitle: str,
):
    result = ctl.search(
        keyword=keyword,
        count=count,
        regex=regex,
        dupe=dupe,
        min_episode=min_episode,
        max_episode=max_episode,
        tag=tag,
        subtitle=subtitle,
    )
    if result["status"] != "success":
        globals()["print_{}".format(result["status"])](result["message"])
    data = result["data"]
    for i in data:
        print(i.title)
    if download:
        download_prepare(data)
