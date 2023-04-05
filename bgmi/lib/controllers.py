import itertools
import os.path
import time
from operator import itemgetter
from typing import Any, Dict, List, Optional

import filetype
import requests.exceptions
import sqlalchemy as sa

from bgmi.config import Source, cfg
from bgmi.lib.constants import BANGUMI_UPDATE_TIME, SUPPORT_WEBSITE
from bgmi.lib.download import Episode, download_episodes
from bgmi.lib.fetch import website
from bgmi.lib.table import (
    FOLLOWED_STATUS,
    STATUS_DELETED,
    STATUS_FOLLOWED,
    STATUS_NOT_DOWNLOAD,
    STATUS_UPDATED,
    Bangumi,
    Download,
    Followed,
    NotFoundError,
    Session,
    Subtitle,
    recreate_source_relatively_table,
)
from bgmi.script import ScriptRunner
from bgmi.utils import (
    COLOR_END,
    GREEN,
    convert_cover_url_to_path,
    download_cover,
    episode_filter_regex,
    logger,
    normalize_path,
    print_error,
    print_info,
    print_success,
    print_warning,
)

ControllerResult = Dict[str, Any]


def add(name: str, episode: Optional[int] = None) -> ControllerResult:
    """
    ret.name :str
    """
    # action add
    # add bangumi by a list of bangumi name
    logger.debug("add name: {} episode: {}", name, episode)
    if not Bangumi.get_updating_bangumi():
        website.fetch(group_by_weekday=False)

    try:
        bangumi_obj = Bangumi.fuzzy_get(name=name)
        name = bangumi_obj.name
    except Bangumi.NotFoundError:
        result = {
            "status": "error",
            "message": f"{name} not found, please check the name",
        }
        return result

    with Session.begin() as session:
        followed_obj: Optional[Followed] = session.scalar(
            sa.select(Followed).where(Followed.bangumi_name == bangumi_obj.name).limit(1)
        )
        if followed_obj is None:
            followed_obj = Followed(status=STATUS_FOLLOWED, bangumi_name=bangumi_obj.name, episode=0)
            session.add(followed_obj)
        else:
            if followed_obj.status == STATUS_FOLLOWED:
                result = {
                    "status": "warning",
                    "message": f"{bangumi_obj.name} already followed",
                }
                return result
            else:
                followed_obj.status = STATUS_FOLLOWED

    if episode is None:
        episodes = website.get_maximum_episode(bangumi_obj, max_page=cfg.max_path)
        followed_obj.episode = max(e.episode for e in episodes) if episodes else 0
    else:
        followed_obj.episode = episode

    followed_obj.save()

    result = {"status": "success", "message": f"add {bangumi_obj.name} to subscribing bangumi list"}
    logger.debug(result)
    return result


def filter_(
    name: str,
    subtitle: Optional[str] = None,
    include: Optional[str] = None,
    exclude: Optional[str] = None,
    regex: Optional[str] = None,
) -> ControllerResult:
    result = {"status": "success", "message": ""}  # type: Dict[str, Any]
    try:
        bangumi_obj = Bangumi.fuzzy_get(name=name)
    except Bangumi.NotFoundError:
        result["status"] = "error"
        result["message"] = f"Bangumi {name} does not exist."
        return result

    try:
        followed_filter_obj = Followed.get(Followed.bangumi_name == bangumi_obj.name)
    except Followed.NotFoundError:
        result["status"] = "error"
        result["message"] = "Bangumi {name} has not subscribed, try 'bgmi add \"{name}\"'.".format(
            name=bangumi_obj.name
        )
        return result

    if subtitle is not None:
        _subtitle = [s.strip() for s in subtitle.split(",")]
        _subtitle = [s.id for s in Subtitle.get_subtitle_by_name(_subtitle)]
        followed_filter_obj.subtitle = [s for s in _subtitle if s in bangumi_obj.subtitle_group]

    if include is not None:
        followed_filter_obj.include = [x.strip() for x in include.split(",")]

    if exclude is not None:
        followed_filter_obj.exclude = [x.strip() for x in exclude.split(",")]

    if regex is not None:
        followed_filter_obj.regex = regex

    followed_filter_obj.save()
    subtitle_list = [s.name for s in Subtitle.get_subtitle_by_id(bangumi_obj.subtitle_group)]

    result["data"] = {
        "name": bangumi_obj.name,
        "subtitle_group": subtitle_list,
        "followed": (
            [s.name for s in Subtitle.get_subtitle_by_id(followed_filter_obj.subtitle)]
            if followed_filter_obj.subtitle
            else []
        ),
        "include": followed_filter_obj.include,
        "exclude": followed_filter_obj.exclude,
        "regex": followed_filter_obj.regex,
    }
    logger.debug(result)
    return result


def delete(name: str = "", clear_all: bool = False, batch: bool = False) -> ControllerResult:
    """
    :param name:
    :param clear_all:
    :param batch:
    """
    # action delete
    # just delete subscribed bangumi or clear all the subscribed bangumi
    result = {}
    logger.debug("delete %s", name)
    if clear_all:
        if Followed.delete_followed(batch=batch):
            result["status"] = "warning"
            result["message"] = "all subscriptions have been deleted"
        else:
            print_error("user canceled")
    elif name:
        try:
            followed = Followed.get(Followed.bangumi_name == name)
            followed.status = STATUS_DELETED
            followed.save()
            result["status"] = "warning"
            result["message"] = f"Bangumi {name} has been deleted"
        except Followed.NotFoundError:
            result["status"] = "error"
            result["message"] = f"Bangumi {name} does not exist"
    else:
        result["status"] = "warning"
        result["message"] = "Nothing has been done."

    logger.debug(result)

    return result


def cal(force_update: bool = False, cover: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
    logger.debug("cal force_update: {}", force_update)

    weekly_list = Bangumi.get_updating_bangumi()
    if not weekly_list:
        print_warning("Warning: no bangumi schedule, fetching ...")
        force_update = True

    if force_update:
        print_info("Fetching bangumi info ...")
        website.fetch()

    weekly_list = Bangumi.get_updating_bangumi()

    if cover is not None:
        # download cover to local
        cover_to_be_download = cover
        for daily_bangumi in weekly_list.values():
            for bangumi in daily_bangumi:
                _, file_path = convert_cover_url_to_path(bangumi["cover"])

                if not (os.path.exists(file_path) and filetype.is_image(file_path)):
                    cover_to_be_download.append(bangumi["cover"])

        if cover_to_be_download:
            print_info("Updating cover ...")
            download_cover(cover_to_be_download)

    runner = ScriptRunner()
    patch_list = runner.get_models_dict()
    for i in patch_list:
        weekly_list[i["update_time"].lower()].append(i)
    logger.debug(weekly_list)

    # for web api, return all subtitle group info
    r = weekly_list  # type: Dict[str, List[Dict[str, Any]]]
    for day, value in weekly_list.items():
        for index, bangumi in enumerate(value):
            bangumi["cover"] = normalize_path(bangumi["cover"])
            subtitle_group = [
                {"name": x.name, "id": x.id} for x in Subtitle.get_subtitle_by_id(bangumi["subtitle_group"])
            ]

            r[day][index]["subtitle_group"] = subtitle_group
    logger.debug(r)
    return r


def mark(name: str, episode: int) -> ControllerResult:
    """

    :param name: name of the bangumi you want to mark
    :param episode: bangumi episode you want to mark
    """
    result = {}

    try:
        followed_obj = Followed.get(Followed.bangumi_name == name)
    except Followed.NotFoundError:
        runner = ScriptRunner()
        followed_obj = runner.get_model(name)  # type: ignore
        if not followed_obj:
            result["status"] = "error"
            result["message"] = f"Subscribe or Script <{name}> does not exist."
            return result

    followed_obj.episode = episode
    followed_obj.save()

    result["status"] = "success"
    result["message"] = f"{name} has been mark as episode: {episode}"
    return result


def search(
    keyword: str,
    count: int = cfg.max_path,
    regex: Optional[str] = None,
    dupe: bool = False,
    min_episode: Optional[int] = None,
    max_episode: Optional[int] = None,
    tag: bool = False,
    subtitle: Optional[str] = None,
) -> ControllerResult:
    try:
        if tag:
            data = website.search_by_tag(keyword, subtitle=subtitle, count=count)
        else:
            data = website.search_by_keyword(keyword, count=count)
        data = episode_filter_regex(data, regex=regex)
        if min_episode is not None:
            data = [x for x in data if x.episode >= min_episode]
        if max_episode is not None:
            data = [x for x in data if x.episode <= max_episode]

        if not dupe:
            data = Episode.remove_duplicated_bangumi(data)
        data.sort(key=lambda x: x.episode)
        return {
            "status": "success",
            "message": "",
            "options": {
                "keyword": keyword,
                "count": count,
                "regex": regex,
                "dupe": dupe,
                "min_episode": min_episode,
                "max_episode": max_episode,
            },
            "data": data,
        }
    except Exception as e:
        if os.environ.get("DEBUG"):
            raise
        return {
            "status": "error",
            "message": str(e),
            "options": {
                "keyword": keyword,
                "count": count,
                "regex": regex,
                "dupe": dupe,
                "min_episode": min_episode,
                "max_episode": max_episode,
            },
            "data": [],
        }


def source(data_source: str) -> ControllerResult:
    result = {}
    if data_source in list(map(itemgetter("id"), SUPPORT_WEBSITE)):
        recreate_source_relatively_table()
        cfg.data_source = Source(data_source)
        cfg.save()
        print_success("data source switch succeeds")
        result["status"] = "success"
        result["message"] = f"you have successfully change your data source to {data_source}"
    else:
        result["status"] = "error"
        result["message"] = "please check your input. data source should be one of {}".format(
            [x["id"] for x in SUPPORT_WEBSITE]
        )
    return result


def update(names: List[str], download: Optional[bool] = False, not_ignore: bool = False) -> ControllerResult:
    logger.debug("updating bangumi info with args: download: %r", download)
    downloaded: List[Episode] = []
    result: Dict[str, Any] = {
        "status": "info",
        "message": "",
        "data": {"updated": [], "downloaded": downloaded},
    }

    ignore = not bool(not_ignore)
    print_info("marking bangumi status ...")
    now = int(time.time())

    for follow in Followed.get_all_followed():
        if follow.updated_time and int(follow.updated_time + 60 * 60 * 24) < now:
            follow.status = STATUS_FOLLOWED
            follow.save()

    for script in ScriptRunner().scripts:
        obj = script.Model().obj
        if obj.updated_time and int(obj.updated_time + 60 * 60 * 24) < now:
            obj.status = STATUS_FOLLOWED
            obj.save()

    print_info("updating subscriptions ...")

    if not names:
        updated_bangumi_obj = Followed.get_all_followed()
    else:
        updated_bangumi_obj = []
        for n in names:
            try:
                f = Followed.get(Followed.bangumi_name == n)
                updated_bangumi_obj.append(f)
            except Followed.NotFoundError:
                logger.warning("missing followed bangumi '{}'", n)

    if download:
        failed = [Episode.parse_obj(x) for x in Download.get_all_downloads(status=STATUS_NOT_DOWNLOAD)]
        if failed:
            print_info("try to re-downloading previous failed torrents ...")
            download_episodes(failed)

    runner = ScriptRunner()
    script_download_queue = runner.run()
    if script_download_queue and download:
        download_episodes(script_download_queue)
        downloaded.extend(script_download_queue)
        print_info("downloading ...")

    for subscribe in updated_bangumi_obj:
        download_queue = []
        print_info(f"fetching {subscribe.bangumi_name} ...")
        try:
            bangumi_obj = Bangumi.get(Bangumi.name == subscribe.bangumi_name)
        except NotFoundError:
            logger.error("Bangumi<{}> does not exists.", subscribe.bangumi_name)
            continue
        try:
            followed_obj = Followed.get(Followed.bangumi_name == subscribe.bangumi_name)
        except NotFoundError:
            logger.error("Followed<{}> is not followed.", subscribe.bangumi_name)
            continue

        try:
            all_episode_data = website.get_maximum_episode(
                bangumi=bangumi_obj, ignore_old_row=ignore, max_page=cfg.max_path
            )
        except requests.exceptions.ConnectionError as e:
            print_warning(f"error {e} to fetch {bangumi_obj.name}, skip")
            continue

        if all_episode_data:
            episode = max(e.episode for e in all_episode_data)
        else:
            episode = 0

        if episode > subscribe.episode:
            episode_range = range(subscribe.episode, episode + 1)
            print_success(f"{subscribe.bangumi_name} updated, episode: {episode:d}")
            followed_obj.episode = episode
            followed_obj.status = STATUS_UPDATED
            followed_obj.updated_time = int(time.time())
            followed_obj.save()
            result["data"]["updated"].append({"bangumi": subscribe.bangumi_name, "episode": episode})

            groups: Dict[int, List[Episode]] = {
                key: list(value) for key, value in itertools.groupby(all_episode_data, lambda x: x.episode)
            }

            for i in episode_range:
                episodes = groups.get(i)
                if episodes:
                    download_queue.append(episodes.pop())

        if download:
            download_episodes(download_queue)
            downloaded.extend(download_queue)

    return result


def status_(name: str, status: int = STATUS_DELETED) -> ControllerResult:
    result = {"status": "success", "message": ""}

    if (status not in FOLLOWED_STATUS) or (not status):
        result["status"] = "error"
        result["message"] = f"Invalid status: {status}"
        return result

    status = int(status)

    followed_obj = Followed.get(Followed.bangumi_name == name)
    if not followed_obj:
        result["status"] = "error"
        result["message"] = f"Followed<{name}> does not exists"
        return result

    followed_obj.status = status
    followed_obj.save()
    result["message"] = f"Followed<{name}> has been marked as status {status}"
    return result


def list_() -> ControllerResult:
    result = {}
    weekday_order = BANGUMI_UPDATE_TIME
    followed_bangumi = website.followed_bangumi()

    script_bangumi = ScriptRunner().get_models_dict()

    if not followed_bangumi and not script_bangumi:
        result["status"] = "warning"
        result["message"] = "you have not subscribed any bangumi"
        return result

    for i in script_bangumi:
        i["subtitle_group"] = [{"name": "<BGmi Script>"}]
        followed_bangumi[i["update_time"].lower()].append(i)

    result["status"] = "info"
    result["message"] = ""
    for weekday in weekday_order:
        if followed_bangumi[weekday.lower()]:
            result["message"] += f"{GREEN}{weekday}. {COLOR_END}"
            for j, bangumi in enumerate(followed_bangumi[weekday.lower()]):
                if bangumi["status"] in (STATUS_UPDATED, STATUS_FOLLOWED) and "episode" in bangumi:
                    bangumi["name"] = f"{bangumi['name']}({bangumi['episode']:d})"
                if j > 0:
                    result["message"] += " " * 5
                f = [x["name"] for x in bangumi["subtitle_group"]]
                result["message"] += "{}: {}\n".format(bangumi["name"], ", ".join(f) if f else "<None>")

    return result
