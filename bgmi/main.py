import datetime
import itertools
import os
import platform
import sys
from operator import itemgetter
from typing import List, Mapping, Optional, Tuple

import click
import pydantic
import tomlkit
import wcwidth
from loguru import logger
from pycomplete import Completer
from tornado import template

from bgmi import __version__
from bgmi.config import BGMI_PATH, CONFIG_FILE_PATH, Config, cfg, write_default_config
from bgmi.lib import controllers as ctl
from bgmi.lib.constants import BANGUMI_UPDATE_TIME, SPACIAL_APPEND_CHARS, SPACIAL_REMOVE_CHARS, SUPPORT_WEBSITE
from bgmi.lib.download import download_prepare
from bgmi.lib.fetch import website
from bgmi.lib.models import STATUS_DELETED, STATUS_FOLLOWED, STATUS_UPDATED, Bangumi, Filter, Followed, Subtitle
from bgmi.lib.update import update_database
from bgmi.script import ScriptRunner
from bgmi.setup import create_dir, init_db, install_crontab
from bgmi.utils import (
    COLOR_END,
    GREEN,
    RED,
    YELLOW,
    check_update,
    get_terminal_col,
    get_web_admin,
    print_error,
    print_info,
    print_success,
    print_version,
    print_warning,
)

__all__ = ["main_for_test", "main", "print_success"]


def main() -> None:
    logger.remove()
    logger.add(
        sys.stderr, format="<blue>{time:YYYY-MM-DD HH:mm:ss}</blue> {level:7} | <level>{message}</level>", level="INFO"
    )
    logger.add(cfg.log_path.parent.joinpath("{time:YYYY-MM-DD}.log"), format="{time} {level} {message}", level="INFO")

    cli.main(prog_name="bgmi")


def main_for_test(args: Optional[List[str]] = None) -> None:
    cli.main(args=args, prog_name="bgmi", standalone_mode=False)


@click.group(name="bgmi")
@click.version_option(__version__, package_name="bgmi", prog_name="bgmi", message=print_version())
@click.pass_context
def cli(ctx: click.Context) -> None:
    if ctx.invoked_subcommand not in ["install", "upgrade", "completion"]:
        check_update()


@cli.command(help="Install BGmi and frontend")
def install() -> None:
    need_to_init = False
    if not os.path.exists(BGMI_PATH):
        need_to_init = True
        print_warning(f"BGMI_PATH {BGMI_PATH} does not exist, installing")

    create_dir()
    init_db()
    if need_to_init:
        install_crontab()

    write_default_config()
    update_database()
    get_web_admin(method="install")


@cli.command(help="upgrade from previous version")
def upgrade() -> None:
    create_dir()
    update_database()
    check_update()


@cli.command(
    help="Select date source bangumi_moe or mikan_project",
)
@click.argument("bangumi_source", required=True, type=click.Choice([x["id"] for x in SUPPORT_WEBSITE]))
def source(bangumi_source: str) -> None:
    result = ctl.source(data_source=bangumi_source)
    globals()["print_{}".format(result["status"])](result["message"])


@cli.group()
def config() -> None:
    ...


@config.command("print")
def config_print() -> None:
    if CONFIG_FILE_PATH.exists():
        print(CONFIG_FILE_PATH.read_text(encoding="utf-8"))
        return
    print("config file not exist")


@config.command("set")
@click.argument("keys", nargs=-1)
@click.option("--value", required=True)
def _config_set(keys: List[str], value: str) -> None:
    config_set(keys, value)


def config_set(keys: List[str], value: str) -> None:
    doc = tomlkit.loads(CONFIG_FILE_PATH.read_text(encoding="utf-8"))

    if keys[0] == "source":
        print_error("you can't change source with this command, use `bgmi source ...`", stop=True)

    res = doc
    for key in keys[:-1]:
        res = res.setdefault(key, {})
        if not isinstance(res, Mapping):
            print_error(f"value of key '{key}' is not object, can't update its attribute")

    res[keys[-1]] = value

    try:
        Config.parse_obj(doc)
    except pydantic.ValidationError as e:
        print(e)
        print("config is not valid after change, won't write to config file")
        return

    CONFIG_FILE_PATH.write_text(tomlkit.dumps(doc), encoding="utf-8")


@config.command("get")
@click.argument("keys", nargs=-1)
def config_get(keys: List[str]) -> None:
    doc = tomlkit.loads(CONFIG_FILE_PATH.read_text(encoding="utf-8"))
    res = doc

    for key in keys:
        res = doc.get(key, {})

    print("config", ".".join(keys), res)


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
) -> None:
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


@cli.command("mark")
@click.argument("name", required=True)
@click.argument("episode", type=int, required=True)
def mark(name: str, episode: int) -> None:
    result = ctl.mark(name=name, episode=episode)
    globals()["print_{}".format(result["status"])](result["message"])


@cli.command()
@click.argument("names", nargs=-1)
@click.option(
    "--episode",
    type=int,
    help="add bangumi and mark it as specified episode",
)
@click.option(
    "--save-path",
    type=str,
    help="add config.save_path_map for bangumi, example: './{bangumi_name}/S1/' './名侦探柯南/S1/'",
)
def add(names: List[str], episode: Optional[int], save_path: Optional[str]) -> None:
    """
    subscribe bangumi

    names: list of bangumi names to subscribe

    --save-path 同时修改 config 中的 `save_path_map`。
    """
    for name in names:
        result = ctl.add(name=name, episode=episode)
        globals()["print_{}".format(result["status"])](result["message"])
        if save_path:
            if result["status"] in ["success", "warning"]:
                bangumi = Bangumi.fuzzy_get(name=name)
                config_set(["save_path_map", bangumi.name], value=save_path.format(bangumi_name=bangumi.name))


@cli.command()
@click.argument("name", nargs=-1)
@click.option(
    "--clear-all",
    "clear",
    is_flag=True,
    default=False,
    help="Clear all the subscriptions, name will be ignored If you provide this flag",
)
@click.option("--yes", is_flag=True, default=False, help="No confirmation")
def delete(name: List[str], clear: bool, yes: bool) -> None:
    """
    name: list of bangumi names to unsubscribe
    """
    if clear:
        ctl.delete("", clear_all=clear, batch=yes)
    else:
        for bangumi_name in name:
            result = ctl.delete(name=bangumi_name)
            globals()["print_{}".format(result["status"])](result["message"])


@cli.command("list", help="list subscribed bangumi")
def list_command() -> None:
    result = ctl.list_()
    print(result["message"])


@cli.command("filter", help="set bangumi episode filters")
@click.argument("name", required=True)
@click.option("--subtitle", help='Subtitle group name, split by ",".')
@click.option(
    "--include",
    help='Filter by keywords which in the title, split by ",".',
)
@click.option("--exclude", help='Filter by keywords which not int the title, split by ",".')
@click.option("--regex", help="Filter by regular expression")
def filter_cmd(
    name: str,
    subtitle: Optional[str],
    regex: Optional[str],
    include: Optional[str],
    exclude: Optional[str],
) -> None:
    """
    name: bangumi name to update filter
    """
    result = ctl.filter_(
        name=name,
        subtitle=subtitle,
        include=include,
        exclude=exclude,
        regex=regex,
    )
    if "data" not in result:
        globals()["print_{}".format(result["status"])](result["message"])
    else:
        print_info("Usable subtitle group: {}".format(", ".join(result["data"]["subtitle_group"])))
        followed_filter_obj = Filter.get(bangumi_name=result["data"]["name"])
        print_filter(followed_filter_obj)


def print_filter(followed_filter_obj: Filter) -> None:
    print(
        "Followed subtitle group: {}".format(
            ", ".join(x["name"] for x in Subtitle.get_subtitle_by_id(followed_filter_obj.subtitle.split(", ")))
            if followed_filter_obj.subtitle
            else "None"
        )
    )
    print(f"Include keywords: {followed_filter_obj.include}")
    print(f"Exclude keywords: {followed_filter_obj.exclude}")
    print(f"Regular expression: {followed_filter_obj.regex}")


@cli.command("cal")
@click.option(
    "-f",
    "--force-update",
    "force_update",
    is_flag=True,
    show_default=True,
    default=False,
    type=bool,
    help="get latest bangumi calendar",
)
@click.option(
    "--today",
    "today",
    is_flag=True,
    show_default=True,
    default=False,
    type=bool,
    help="show bangumi calendar for today.",
)
@click.option(
    "--download-cover",
    "download_cover",
    is_flag=True,
    show_default=True,
    default=False,
    type=bool,
    help="download the cover to local",
)
def calendar(force_update: bool, today: bool, download_cover: bool) -> None:
    runner = ScriptRunner()
    cover: Optional[List[str]] = None

    if download_cover:
        cover = runner.get_download_cover()

    weekly_list = ctl.cal(force_update=force_update, cover=cover)

    def shift(seq: Tuple[str, ...], n: int) -> Tuple[str, ...]:
        n %= len(seq)
        return seq[n:] + seq[:n]

    order_without_unknown = BANGUMI_UPDATE_TIME[:-1]
    if today:
        weekday_order = (order_without_unknown[datetime.datetime.today().weekday()],)  # type: Tuple[str, ...]
    else:
        weekday_order = shift(order_without_unknown, datetime.datetime.today().weekday())

    col = max(wcwidth.wcswidth(bangumi["name"]) for value in weekly_list.values() for bangumi in value)
    env_columns = col if os.environ.get("TRAVIS_CI", False) else get_terminal_col()

    if env_columns < col:
        print_warning("terminal window is too small.")
        env_columns = col

    row = int(env_columns / col if env_columns / col <= 3 else 3)

    def print_line() -> None:
        num = col - 3
        split = "-" * num + "   "
        print(split * row)

    for weekday in weekday_order + ("Unknown",):
        if weekly_list[weekday.lower()]:
            print(
                "{}{}. {}".format(
                    GREEN,
                    weekday if not today else f"Bangumi Schedule for Today ({weekday})",
                    COLOR_END,
                ),
                end="",
            )
            print()
            print_line()
            for i, bangumi in enumerate(weekly_list[weekday.lower()]):
                if bangumi["status"] in (STATUS_UPDATED, STATUS_FOLLOWED) and "episode" in bangumi:
                    bangumi["name"] = "{}({:d})".format(bangumi["name"], bangumi["episode"])

                width = wcwidth.wcswidth(bangumi["name"])
                space_count = col - 2 - width

                for s in SPACIAL_APPEND_CHARS:
                    if s in bangumi["name"]:
                        space_count += bangumi["name"].count(s)

                for s in SPACIAL_REMOVE_CHARS:
                    if s in bangumi["name"]:
                        space_count -= bangumi["name"].count(s)

                if bangumi["status"] == STATUS_FOLLOWED:
                    bangumi["name"] = "{}{}{}".format(YELLOW, bangumi["name"], COLOR_END)

                if bangumi["status"] == STATUS_UPDATED:
                    bangumi["name"] = "{}{}{}".format(GREEN, bangumi["name"], COLOR_END)
                try:
                    print(" " + bangumi["name"], " " * space_count, end="")
                except UnicodeEncodeError:
                    continue

                if (i + 1) % row == 0 or i + 1 == len(weekly_list[weekday.lower()]):
                    print()
            print()


@cli.command("fetch")
@click.argument("name")
@click.option(
    "--not-ignore", "not_ignore", is_flag=True, help="Do not ignore the old bangumi detail rows (3 month ago)"
)
def fetch(name: str, not_ignore: bool) -> None:
    """
    name: bangumi name to fetch
    """

    try:
        bangumi_obj = Bangumi.get(name=name)
    except Bangumi.DoesNotExist:
        print_error(f"Bangumi {name} not exist", stop=True)
        return

    try:
        Followed.get(bangumi_name=bangumi_obj.name)
    except Followed.DoesNotExist:
        print_error(f"Bangumi {name} is not followed")
        return

    followed_filter_obj = Filter.get(bangumi_name=name)
    print_filter(followed_filter_obj)

    print_info(f"Fetch bangumi {bangumi_obj.name} ...")
    _, data = website.get_maximum_episode(bangumi_obj, ignore_old_row=not bool(not_ignore))

    if not data:
        print_warning("Nothing.")

    max_episode = max(i.episode for i in data)
    digest = len(str(max_episode))

    for i in data:
        episode = str(i.episode).rjust(digest)
        print(f"{episode} | {i.title}")


@cli.command("update", help="Update bangumi calendar and subscribed bangumi episode.")
@click.argument(
    "names",
    nargs=-1,
)
@click.option(
    "-d", "--download", is_flag=True, default=False, help="Download specified episode of the bangumi when updated"
)
@click.option(
    "--not-ignore", "not_ignore", is_flag=True, help="Do not ignore the old bangumi detail rows (3 month ago)"
)
def update(names: List[str], download: bool, not_ignore: bool) -> None:
    """
    name: optional bangumi name list you want to update
    """
    ctl.update(names, download=download, not_ignore=not_ignore)


@cli.command("gen")
@click.argument("tpl", type=click.Choice(["nginx.conf"]))
@click.option("--server-name", "server_name")
def generate_config(tpl: str, server_name: str) -> None:
    template_file_path = os.path.join(os.path.dirname(__file__), "others", "nginx.conf")

    with open(template_file_path, encoding="utf8") as template_file:
        shell_template = template.Template(template_file.read(), autoescape="")

    template_with_content = shell_template.generate(
        server_name=server_name,
        os_sep=os.sep,
        front_static_path=str(cfg.front_static_path.as_posix()),
        save_path=str(cfg.save_path.as_posix()),
    )

    print(template_with_content.decode("utf-8"))


@cli.command("history", help="list your history of following bangumi")
def history() -> None:
    m = (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    )
    data = Followed.select(Followed).order_by(Followed.updated_time.asc())
    bangumi_data = Bangumi.get_updating_bangumi()
    year = None
    month = None

    updating_bangumi = list(map(itemgetter("name"), itertools.chain(*bangumi_data.values())))

    print("Bangumi Timeline")
    for i in data:
        if i.status == STATUS_DELETED:
            slogan = "ABANDON"
            color = RED
        else:
            if i.bangumi_name in updating_bangumi:
                slogan = "FOLLOWING"
                color = YELLOW
            else:
                slogan = "FINISHED"
                color = GREEN

        if not i.updated_time:
            date = datetime.datetime.fromtimestamp(0)
        else:
            date = datetime.datetime.fromtimestamp(int(i.updated_time))

        if date.year != 1970:
            if date.year != year:
                print(f"{GREEN}{str(date.year)}{COLOR_END}")
                year = date.year

            if date.year == year and date.month != month:
                print(f"  |\n  |--- {YELLOW}{m[date.month - 1]}{COLOR_END}\n  |      |")
                month = date.month

            print(f"  |      |--- [{color}{slogan:<9}{COLOR_END}] ({i.episode:<2}) {i.bangumi_name}")


@cli.group("debug")
def debug() -> None:
    ...


@debug.command("info")
def debug_info() -> None:
    print(f"bgmi version: `{__version__}`")
    print(f"python version: `{sys.version}`")
    print(f"os: `{platform.platform()}`")
    print(f"arch: `{platform.architecture()}`")


@cli.command("completion")
@click.argument("shell", required=True)
def completion(shell: str) -> None:
    completer = Completer(cli)
    print(completer.render(shell))
