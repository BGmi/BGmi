import datetime
import itertools
import os
import sys
from operator import itemgetter
from typing import Any, Dict, List, Optional, Tuple

import wcwidth
from tornado import template

import bgmi.config
from bgmi.config import CONFIG_FILE_PATH, print_config
from bgmi.lib.constants import (
    ACTION_ADD,
    ACTION_CAL,
    ACTION_COMPLETE,
    ACTION_CONFIG,
    ACTION_CONFIG_GEN,
    ACTION_DELETE,
    ACTION_DOWNLOAD,
    ACTION_FETCH,
    ACTION_FILTER,
    ACTION_HISTORY,
    ACTION_LIST,
    ACTION_MARK,
    ACTION_SEARCH,
    ACTION_SOURCE,
    ACTION_UPDATE,
    ACTIONS,
    BANGUMI_UPDATE_TIME,
    SPACIAL_APPEND_CHARS,
    SPACIAL_REMOVE_CHARS,
    SUPPORT_WEBSITE,
    actions_and_arguments,
)
from bgmi.lib.controllers import add, cal, delete, filter_, list_, mark, search, source, update
from bgmi.lib.download import download_prepare
from bgmi.lib.fetch import website
from bgmi.lib.models import STATUS_DELETED, STATUS_FOLLOWED, STATUS_UPDATED, Bangumi, Filter, Followed, Subtitle
from bgmi.script import ScriptRunner
from bgmi.utils import (
    COLOR_END,
    GREEN,
    RED,
    YELLOW,
    get_terminal_col,
    logger,
    print_error,
    print_info,
    print_success,
    print_warning,
)


def source_wrapper(ret: Any) -> None:
    result = source(data_source=ret.source)
    globals()["print_{}".format(result["status"])](result["message"])


def config_wrapper(ret: Any) -> None:
    name = ret.name
    value = ret.value

    if name or value:
        print("use config command to change config has been removed, please edit config file directly")
        print(f"config file location: {str(CONFIG_FILE_PATH)!r}")
    else:
        print(print_config())


def search_wrapper(ret: Any) -> None:
    result = search(
        keyword=ret.keyword,
        count=ret.count,
        regex=ret.regex_filter,
        dupe=ret.dupe,
        min_episode=ret.min_episode,
        max_episode=ret.max_episode,
        tag=ret.tag,
        subtitle=ret.subtitle,
    )
    if result["status"] != "success":
        globals()["print_{}".format(result["status"])](result["message"])
    data = result["data"]
    for i in data:
        print_success(i.title)
    if ret.download:
        download_prepare(data)


def mark_wrapper(ret: Any) -> None:
    result = mark(name=ret.name, episode=ret.episode)
    globals()["print_{}".format(result["status"])](result["message"])


def delete_wrapper(ret: Any) -> None:
    if ret.clear_all:
        delete("", clear_all=ret.clear_all, batch=ret.batch)
    else:
        for bangumi_name in ret.name:
            result = delete(name=bangumi_name)
            globals()["print_{}".format(result["status"])](result["message"])


def add_wrapper(ret: Any) -> None:
    for bangumi_name in ret.name:
        result = add(name=bangumi_name, episode=ret.episode)
        globals()["print_{}".format(result["status"])](result["message"])


def list_wrapper(*args: Any) -> None:
    result = list_()
    print(result["message"])


def cal_wrapper(ret: Any) -> None:
    force_update = ret.force_update
    today = ret.today
    save = not ret.no_save

    runner = ScriptRunner()
    cover: Optional[List[str]] = None

    if ret.download_cover:
        cover = runner.get_download_cover()

    weekly_list = cal(force_update=force_update, save=save, cover=cover)

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


def filter_wrapper(ret: Any) -> None:
    result = filter_(
        name=ret.name,
        subtitle=ret.subtitle,
        include=ret.include,
        exclude=ret.exclude,
        regex=ret.regex,
    )
    if "data" not in result:
        globals()["print_{}".format(result["status"])](result["message"])
    else:
        print_info("Usable subtitle group: {}".format(", ".join(result["data"]["subtitle_group"])))
        followed_filter_obj = Filter.get(bangumi_name=result["data"]["name"])
        print_filter(followed_filter_obj)


def update_wrapper(ret: Any) -> None:
    update(name=ret.name, download=ret.download, not_ignore=ret.not_ignore)


def download_manager(ret: Any) -> None:
    print_info("not support yet")


def fetch_(ret: Any) -> None:
    try:
        bangumi_obj = Bangumi.get(name=ret.name)
    except Bangumi.DoesNotExist:
        print_error(f"Bangumi {ret.name} not exist")
        return

    try:
        Followed.get(bangumi_name=bangumi_obj.name)
    except Followed.DoesNotExist:
        print_error(f"Bangumi {ret.name} is not followed")
        return

    followed_filter_obj = Filter.get(bangumi_name=ret.name)
    print_filter(followed_filter_obj)

    print_info(f"Fetch bangumi {bangumi_obj.name} ...")
    _, data = website.get_maximum_episode(bangumi_obj, ignore_old_row=not bool(ret.not_ignore))

    if not data:
        print_warning("Nothing.")
    for i in data:
        print_success(i.title)


def complete(ret: Any) -> None:
    # coding=utf-8
    """eval "$(bgmi complete)" to complete bgmi in bash"""
    updating_bangumi_names = [x["name"] for x in Bangumi.get_updating_bangumi(order=False)]

    actions_and_opts: Dict[str, list] = {}
    helper = {}
    for action_dict in actions_and_arguments:
        actions_and_opts[action_dict["action"]] = []
        for arg in action_dict.get("arguments", []):
            if isinstance(arg["dest"], str) and arg["dest"].startswith("-"):
                actions_and_opts[action_dict["action"]].append(arg)
            elif isinstance(arg["dest"], list):
                actions_and_opts[action_dict["action"]].append(arg)
        helper[action_dict["action"]] = action_dict.get("help", "")

    current_shell = os.getenv("SHELL", "").lower()
    completions_dir = os.path.join(os.path.dirname(__file__), "..", "others")

    if "bash" in current_shell:  # bash
        template_file_path = os.path.join(completions_dir, "_bgmi_completion_bash.sh")
    elif "zsh" in current_shell:  # zsh
        template_file_path = os.path.join(completions_dir, "_bgmi_completion_zsh.sh")
    else:
        print(f"unsupported shell {current_shell}", file=sys.stderr)
        return

    with open(template_file_path, encoding="utf8") as template_file:
        shell_template = template.Template(template_file.read(), autoescape="")

    template_with_content = shell_template.generate(
        actions=ACTIONS,
        bangumi=updating_bangumi_names,
        actions_and_opts=actions_and_opts,
        source=[x["id"] for x in SUPPORT_WEBSITE],
        helper=helper,
        isinstance=isinstance,
        string_types=(str,),
    )  # type: bytes

    if os.environ.get("DEBUG", False):  # pragma: no cover
        with open("./_bgmi", "wb+") as debug_file:
            debug_file.write(template_with_content)

    print(template_with_content.decode("utf-8"))


def history(ret: Any) -> None:
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

    print_info("Bangumi Timeline")
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


def config_gen(ret: Any) -> None:
    template_file_path = os.path.join(os.path.dirname(__file__), "..", "others", "nginx.conf")

    with open(template_file_path, encoding="utf8") as template_file:
        shell_template = template.Template(template_file.read(), autoescape="")

    template_with_content = shell_template.generate(
        actions=ACTIONS,
        server_name=ret.server_name,
        os_sep=os.sep,
        front_static_path=str(bgmi.config.cfg.front_static_path.as_posix()),
        save_path=str(bgmi.config.cfg.save_path.as_posix()),
    )  # type: bytes

    print(template_with_content.decode("utf-8"))


CONTROLLERS_DICT = {
    ACTION_ADD: add_wrapper,
    ACTION_SOURCE: source_wrapper,
    ACTION_DOWNLOAD: download_manager,
    ACTION_CONFIG: config_wrapper,
    ACTION_DELETE: delete_wrapper,
    ACTION_MARK: mark_wrapper,
    ACTION_SEARCH: search_wrapper,
    ACTION_FILTER: filter_wrapper,
    ACTION_CAL: cal_wrapper,
    ACTION_UPDATE: update_wrapper,
    ACTION_FETCH: fetch_,
    ACTION_LIST: list_wrapper,
    ACTION_COMPLETE: complete,
    ACTION_HISTORY: history,
    ACTION_CONFIG_GEN: config_gen,
}


def controllers(ret: Any) -> None:
    logger.info(ret)
    func = CONTROLLERS_DICT.get(ret.action, None)
    if not callable(func):
        return
    else:
        func(ret)


def print_filter(followed_filter_obj: Filter) -> None:
    print_info(
        "Followed subtitle group: {}".format(
            ", ".join(x["name"] for x in Subtitle.get_subtitle_by_id(followed_filter_obj.subtitle.split(", ")))
            if followed_filter_obj.subtitle
            else "None"
        )
    )
    print_info(f"Include keywords: {followed_filter_obj.include}")
    print_info(f"Exclude keywords: {followed_filter_obj.exclude}")
    print_info(f"Regular expression: {followed_filter_obj.regex}")
