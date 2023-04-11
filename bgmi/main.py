import datetime
import itertools
import os
import platform
import sys
from collections import defaultdict
from operator import itemgetter
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import click
import pydantic
import sqlalchemy as sa
import tomlkit
import wcwidth
from loguru import logger

from bgmi import __version__
from bgmi.config import CONFIG_FILE_PATH, Config, Source, cfg, write_default_config
from bgmi.lib import controllers as ctl
from bgmi.lib.constants import BANGUMI_UPDATE_TIME, SPACIAL_APPEND_CHARS, SPACIAL_REMOVE_CHARS, SUPPORT_WEBSITE
from bgmi.lib.download import download_downloads
from bgmi.lib.fetch import website
from bgmi.lib.table import Bangumi, Download, Followed, Session, Subtitle, recreate_source_relatively_table
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
    if ctx.command not in ["install", "upgrade", "complete"]:
        check_update()


@cli.command(help="Install BGmi and frontend")
@click.option("--no-web", is_flag=True, default=False, help="Do not download web static files")
def install(no_web: bool) -> None:
    need_to_init = False
    if not CONFIG_FILE_PATH.exists():
        need_to_init = True

    create_dir()
    init_db()
    if need_to_init:
        install_crontab()

    write_default_config()
    update_database()

    if not no_web:
        get_web_admin(method="install")


@cli.command(help="upgrade from previous version")
def upgrade() -> None:
    create_dir()
    update_database()
    check_update()


@cli.command(
    help="Select date source bangumi_moe or mikan_project",
)
@click.argument("source", required=True, type=click.Choice([x["id"] for x in SUPPORT_WEBSITE]))
def source_cmd(source: str) -> None:
    if source in list(map(itemgetter("id"), SUPPORT_WEBSITE)):
        recreate_source_relatively_table()
        cfg.data_source = Source(source)
        cfg.save()
        print_success("data source switch succeeds")
        print_success(f"you have successfully change your data source to {source}")
    else:
        print_error(
            "please check your input. data source should be one of {}".format([x["id"] for x in SUPPORT_WEBSITE])
        )


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
        download_downloads(
            [
                Download(
                    bangumi_name=x.name,
                    episode=x.episode,
                    status=Download.STATUS_DOWNLOADING,
                    download=x.download,
                    title=x.title,
                )
                for x in data
            ]
        )


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
    help='add config.save_path_map for bangumi, example: "./{bangumi_name}/S1/" "./名侦探柯南/S1/"',
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
        if save_path and result["status"] in ["success", "warning"]:
            bangumi = Bangumi.get(Bangumi.name.contains(name))
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


def followed_bangumi() -> Dict[str, list]:
    """

    :return: list of bangumi followed
    """
    weekly_list_followed = Bangumi.get_updating_bangumi(status=Followed.STATUS_FOLLOWED)
    weekly_list_updated = Bangumi.get_updating_bangumi(status=Followed.STATUS_UPDATED)
    weekly_list = defaultdict(list)
    for k, v in itertools.chain(weekly_list_followed.items(), weekly_list_updated.items()):
        weekly_list[k].extend(v)
    for bangumi_list in weekly_list.values():
        for bangumi in bangumi_list:
            bangumi["subtitle_group"] = Subtitle.get_subtitle_by_id(bangumi["subtitle_group"])
    return weekly_list


@cli.command("list", help="list subscribed bangumi")
def list_command() -> None:
    weekday_order = BANGUMI_UPDATE_TIME
    followed = followed_bangumi()

    script_bangumi = ScriptRunner().get_models_dict()

    if not followed and not script_bangumi:
        print_warning("you have not subscribed any bangumi")
        return

    for i in script_bangumi:
        i["subtitle_group"] = []
        followed[i["update_day"].lower()].append(i)

    s = ""

    for weekday in weekday_order:
        if followed[weekday.lower()]:
            s += f"{GREEN}{weekday}. {COLOR_END}"
            for j, bangumi in enumerate(followed[weekday.lower()]):
                if bangumi["status"] in (Followed.STATUS_UPDATED, Followed.STATUS_FOLLOWED) and "episode" in bangumi:
                    bangumi["name"] = f"{bangumi['name']}({bangumi['episode']:d})"
                if j > 0:
                    s += " " * 5

                f = [x.name for x in bangumi["subtitle_group"]]

                s += "{}: {}\n".format(bangumi["name"], ", ".join(f) if f else "<None>")

    print(s)


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
        print("Usable subtitle group: {}".format(", ".join(result["data"]["subtitle_group"])))
        print()
        filter_obj = Followed.get(Followed.bangumi_name == result["data"]["name"])
        print_filter(filter_obj)


def print_filter(followed_filter_obj: Followed) -> None:
    print(
        "Followed subtitle group: {}".format(
            [x.name for x in Subtitle.get_subtitle_by_id(followed_filter_obj.subtitle)]
            if followed_filter_obj.subtitle
            else None
        )
    )
    print(f"Include keywords: {followed_filter_obj.include or None}")
    print(f"Exclude keywords: {followed_filter_obj.exclude or None}")
    print(f"Regular expression: {followed_filter_obj.regex or None}")


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

    for weekday in (*weekday_order, "Unknown"):
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

            weekly_list[weekday.lower()].sort(key=lambda x: x["episode"] or -999, reverse=True)

            for i, bangumi in enumerate(weekly_list[weekday.lower()]):
                if bangumi["status"] in (Followed.STATUS_UPDATED, Followed.STATUS_FOLLOWED) and "episode" in bangumi:
                    bangumi["name"] = "{}({:d})".format(bangumi["name"], bangumi["episode"])

                width = wcwidth.wcswidth(bangumi["name"])
                space_count = col - 2 - width

                for s in SPACIAL_APPEND_CHARS:
                    if s in bangumi["name"]:
                        space_count += bangumi["name"].count(s)

                for s in SPACIAL_REMOVE_CHARS:
                    if s in bangumi["name"]:
                        space_count -= bangumi["name"].count(s)

                if bangumi["status"] == Followed.STATUS_FOLLOWED:
                    bangumi["name"] = "{}{}{}".format(YELLOW, bangumi["name"], COLOR_END)

                if bangumi["status"] == Followed.STATUS_UPDATED:
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
        bangumi_obj = Bangumi.get(Bangumi.name == name)
    except Bangumi.NotFoundError:
        print_error(f"Bangumi {name} not exist", stop=True)
        return

    try:
        Followed.get(Followed.bangumi_name == name)
    except Followed.NotFoundError:
        print_error(f"Bangumi {name} is not followed")
        return

    print_info(f"Fetch bangumi {bangumi_obj.name} ...")
    data = website.get_maximum_episode(bangumi_obj, ignore_old_row=not bool(not_ignore))

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
    "-d", "--download", type=bool, default=True, help="Download specified episode of the bangumi when updated"
)
@click.option(
    "--not-ignore", "not_ignore", is_flag=True, help="Do not ignore the old bangumi detail rows (3 month ago)"
)
def update(names: List[str], download: bool, not_ignore: bool) -> None:
    """
    name: optional bangumi name list you want to update
    """
    ctl.update(names, download=download, not_ignore=not_ignore)


template = {
    "nginx.conf": """
    server {
    listen 80;
    server_name { server_name };

    root { front_static_path }{ os_sep };
    autoindex on;
    charset utf-8;

    location /bangumi/ {
        # ~/.bgmi/bangumi/
        alias {{ save_path }}{{ os_sep }};
    }

    location /api {
        proxy_pass http://127.0.0.1:8888;
    }

    location /resource {
        proxy_pass http://127.0.0.1:8888;
    }

    location / {
        # ~/.bgmi/front_static/;
        alias { front_static_path }{ os_sep };
    }

}
"""
}


@cli.command("gen")
@click.argument("tpl", type=click.Choice(["nginx.conf"]))
@click.option("--server-name", "server_name")
def generate_config(tpl: str, server_name: str) -> None:
    if tpl == "nginx.conf":
        template_file_path = os.path.join(os.path.dirname(__file__), "others", "nginx.conf")

        with open(template_file_path, encoding="utf8") as template_file:
            shell_template = template_file.read()

        template_with_content = shell_template.format(
            server_name=server_name,
            os_sep=os.sep,
            front_static_path=str(cfg.front_static_path),
            save_path=str(cfg.save_path),
        )

        print(template_with_content)


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
    with Session.begin() as session:
        data: Sequence[Followed] = session.scalars(sa.select(Followed).order_by(Followed.updated_time.asc())).all()
    bangumi_data = Bangumi.get_updating_bangumi()
    year = None
    month = None

    updating_bangumi = list(map(itemgetter("name"), itertools.chain(*bangumi_data.values())))

    print("Bangumi Timeline")
    for i in data:
        if i.status == Followed.STATUS_DELETED:
            slogan = "ABANDON"
            color = RED
        elif i.bangumi_name in updating_bangumi:
            slogan = "FOLLOWING"
            color = YELLOW
        else:
            slogan = "FINISHED"
            color = GREEN

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
