import itertools
import os.path
import time
from typing import Any, Dict, List, Optional, Union

import filetype
import requests.exceptions
import sqlalchemy as sa

from bgmi.config import cfg
from bgmi.lib.download import download_episode
from bgmi.lib.fetch import website
from bgmi.lib.table import Bangumi, Download, Followed, NotFoundError, Scripts, Session, Subtitle
from bgmi.script import ScriptRunner
from bgmi.utils import (
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
from bgmi.website.model import Episode

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
        bangumi_obj = Bangumi.get(Bangumi.name.contains(name))
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
            followed_obj = Followed(status=Followed.STATUS_FOLLOWED, bangumi_name=bangumi_obj.name)
            session.add(followed_obj)
        elif followed_obj.status == Followed.STATUS_FOLLOWED:
            result = {
                "status": "warning",
                "message": f"{bangumi_obj.name} already followed",
            }
            return result
        else:
            followed_obj.status = Followed.STATUS_FOLLOWED

    if episode is None:
        episodes = website.get_maximum_episode(bangumi_obj, max_page=cfg.max_path)
        followed_obj.episodes = sorted([e.episode for e in episodes]) if episodes else 0  # type: ignore
    else:
        followed_obj.episodes = list(range(0, episode + 1))

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
        bangumi_obj = Bangumi.get(Bangumi.name.contains(name))
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
            followed.status = Followed.STATUS_DELETED
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
        weekly_list[i["update_day"].lower()].append(i)
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


def update(names: List[str], download: Optional[bool] = False, not_ignore: bool = False) -> None:
    logger.debug("updating bangumi info with args: download: {}", download)

    ignore = not bool(not_ignore)
    now = int(time.time())
    print_info("updating subscriptions ...")

    if not names:
        updated_bangumi_obj = [x[0] for x in Followed.get_all_followed()]
    else:
        updated_bangumi_obj = []
        for n in names:
            try:
                f = Followed.get(Followed.bangumi_name == n)
                updated_bangumi_obj.append(f)
            except Followed.NotFoundError:
                logger.warning("missing followed bangumi '{}'", n)

    if download:
        need_re_download = []
        failures = Download.get_all_downloads(status=Download.STATUS_NOT_DOWNLOAD)
        followings: Dict[str, Followed] = {x.bangumi_name: x for x in Followed.all()}

        if failures:
            for fail in failures:
                following = followings.get(fail.bangumi_name)
                if not following:
                    continue

                if fail.episode in following.episodes:
                    continue

                need_re_download.append(fail)

        if need_re_download:
            print_info("try to re-downloading previous failed torrents ...")
            for d in need_re_download:
                download_episode(
                    Episode(
                        title=d.title,
                        episode=d.episode,
                        download=d.download,
                        name=d.bangumi_name,
                    )
                )

    runner = ScriptRunner()

    for script, all_episode_data in runner.run():
        following = Followed.get(Followed.bangumi_name == script.bangumi_name)

        if not download:
            following.episodes = sorted({x.episode for x in all_episode_data} | set(following.episodes))
            following.updated_time = now
            following.save()
        else:
            download_episodes(all_episode_data, following)

    for subscribe in updated_bangumi_obj:
        print_info(f"fetching {subscribe.bangumi_name} ...")
        try:
            bangumi_obj = Bangumi.get(Bangumi.name == subscribe.bangumi_name)
        except NotFoundError:
            logger.error("Bangumi<{}> does not exists.", subscribe.bangumi_name)
            continue
        try:
            following = Followed.get(Followed.bangumi_name == subscribe.bangumi_name)
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

        if not all_episode_data:
            continue

        if not download:
            following.episodes = sorted({x.episode for x in all_episode_data} | set(following.episodes))
            following.save()
        else:
            download_episodes(all_episode_data, following)


def download_episodes(all_episode_data: List[Episode], following: Union[Followed, Scripts]) -> None:
    groups: Dict[int, List[Episode]] = {
        key: list(value) for key, value in itertools.groupby(all_episode_data, lambda x: x.episode)
    }

    for ep, episodes in sorted(groups.items()):
        if ep in following.episodes:
            # already downloaded, skipping
            continue

        print_success(f"{following.bangumi_name} updated, episode: {ep:d}")
        following.status = Followed.STATUS_UPDATED

        if episodes:
            for e in episodes:
                if download_episode(e):
                    following.episodes.append(ep)  # type: ignore
                    break

    following.updated_time = int(time.time())
    following.save()


def status_(name: str, status: int = Followed.STATUS_DELETED) -> ControllerResult:
    result = {"status": "success", "message": ""}

    if (status not in Followed.FOLLOWED_STATUS) or (not status):
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
