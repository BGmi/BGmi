import itertools
import os.path
import time
from operator import attrgetter
from typing import Any, Dict, List, Optional, Union

import filetype
import requests.exceptions
import sqlalchemy as sa

from bgmi.config import cfg
from bgmi.lib.download import download_episode
from bgmi.lib.fetch import website
from bgmi.lib.season import parse_season, strip_season_suffix
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


def _auto_display_name(name: str, display_name: Optional[str]) -> Optional[str]:
    if display_name is not None:
        return display_name

    stripped_name = strip_season_suffix(name)
    if stripped_name != name:
        return stripped_name
    return None


def _season_display_note(
    detected_season: int,
    resolved_season: int,
    display_name: Optional[str],
    auto_display_name: Optional[str],
) -> str:
    if not auto_display_name or display_name is not None:
        return ""
    if detected_season != resolved_season:
        season_note = f"detected season {detected_season}, using season {resolved_season}"
    else:
        season_note = f"detected season {detected_season}"
    return f"{season_note}; path display name normalized to {auto_display_name}"


def add(
    name: str,
    episode: Optional[int] = 0,
    season: Optional[int] = None,
    episode_offset: Optional[int] = None,
    display_name: Optional[str] = None,
) -> ControllerResult:
    """
    ret.name :str
    """
    # action add
    # add bangumi by a list of bangumi name
    logger.debug("add name: {} episode: {} season: {}", name, episode, season)
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

    has_overrides = season is not None or episode_offset is not None or display_name is not None
    detected_season = parse_season(bangumi_obj.name)
    resolved_season = season if season is not None else detected_season
    resolved_display_name = _auto_display_name(bangumi_obj.name, display_name)
    auto_display_name = resolved_display_name if display_name is None else None
    note = _season_display_note(detected_season, resolved_season, display_name, auto_display_name)
    if note:
        logger.info("{}: {}", bangumi_obj.name, note)

    with Session.begin() as session:
        followed_obj: Optional[Followed] = session.scalar(
            sa.select(Followed).where(Followed.bangumi_name == bangumi_obj.name).limit(1)
        )
        if followed_obj is None:
            followed_obj = Followed(
                status=Followed.STATUS_FOLLOWED, bangumi_name=bangumi_obj.name, season=resolved_season
            )
            if episode_offset is not None:
                followed_obj.episode_offset = episode_offset
            if resolved_display_name is not None:
                followed_obj.display_name = resolved_display_name
            session.add(followed_obj)
        elif followed_obj.status == Followed.STATUS_FOLLOWED:
            should_set_auto_display_name = auto_display_name is not None and not followed_obj.display_name
            if has_overrides or should_set_auto_display_name:
                if season is not None:
                    followed_obj.season = season
                if episode_offset is not None:
                    followed_obj.episode_offset = episode_offset
                if display_name is not None:
                    followed_obj.display_name = display_name
                elif should_set_auto_display_name and auto_display_name is not None:
                    followed_obj.display_name = auto_display_name
                session.flush()
                message = f"{bangumi_obj.name} updated"
                if should_set_auto_display_name and note:
                    message = f"{message}; {note}"
                result = {
                    "status": "success",
                    "message": message,
                }
                return result
            result = {
                "status": "warning",
                "message": f"{bangumi_obj.name} already followed",
            }
            return result
        else:
            followed_obj.status = Followed.STATUS_FOLLOWED
            if season is not None:
                followed_obj.season = season
            if episode_offset is not None:
                followed_obj.episode_offset = episode_offset
            if resolved_display_name is not None:
                followed_obj.display_name = resolved_display_name

    if episode is None:
        episodes = website.get_maximum_episode(bangumi_obj, max_page=cfg.max_path)
        followed_obj.episodes = {e.episode for e in episodes}  # type: ignore
    else:
        followed_obj.episodes = set(range(1, episode + 1))

    followed_obj.save()

    message = f"add {bangumi_obj.name} to subscribing bangumi list"
    if note:
        message = f"{message}; {note}"
    result = {"status": "success", "message": message}
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
        followed_filter_obj.include = [x.strip() for x in include.split(",") if x.strip()]

    if exclude is not None:
        followed_filter_obj.exclude = [x.strip() for x in exclude.split(",") if x.strip()]

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


def _seen_payload(followed: Followed, episode: Optional[int] = None) -> ControllerResult:
    episodes = sorted(followed.episodes)
    total_candidates = episodes.copy()
    if episode is not None:
        total_candidates.append(episode)

    with Session.begin() as session:
        max_download_episode = session.scalar(
            sa.select(sa.func.max(Download.episode)).where(Download.bangumi_name == followed.bangumi_name)
        )
    if max_download_episode:
        total_candidates.append(max_download_episode)

    return {
        "bangumi": followed.bangumi_name,
        "total_episode": max(total_candidates) if total_candidates else 0,
        "seen": episodes,
    }


def seen(name: str) -> ControllerResult:
    """Get downloaded episode records for a followed bangumi."""
    try:
        followed = Followed.get(
            Followed.bangumi_name == name,
            Followed.status.isnot(Followed.STATUS_DELETED),
        )
    except Followed.NotFoundError:
        return {"status": "error", "message": f"{name} is not followed"}

    return {
        "status": "success",
        "message": f"Got seen episodes of {name}",
        **_seen_payload(followed),
    }


def seen_forget(name: str, episode: int) -> ControllerResult:
    """Remove an episode from downloaded records so it can be downloaded again."""
    if episode <= 0:
        return {"status": "error", "message": "episode should be greater than 0"}

    try:
        followed = Followed.get(
            Followed.bangumi_name == name,
            Followed.status.isnot(Followed.STATUS_DELETED),
        )
    except Followed.NotFoundError:
        return {"status": "error", "message": f"{name} is not followed"}

    if episode not in followed.episodes:
        return {"status": "error", "message": f"episode {episode} is not in download records"}

    followed.episodes.remove(episode)
    followed.save()

    with Session.begin() as session:
        session.execute(
            sa.update(Download)
            .where(Download.bangumi_name == name, Download.episode == episode)
            .values(status=Download.STATUS_DOWNLOADED, task_id=None)
        )

    return {
        "status": "success",
        "message": f"Forgot episode {episode} of {name}; it will be downloaded on next update",
        "episode": episode,
        **_seen_payload(followed, episode=episode),
    }


def seen_mark(name: str, episode: int) -> ControllerResult:
    """Add an episode to downloaded records so update will treat it as seen."""
    if episode <= 0:
        return {"status": "error", "message": "episode should be greater than 0"}

    try:
        followed = Followed.get(
            Followed.bangumi_name == name,
            Followed.status.isnot(Followed.STATUS_DELETED),
        )
    except Followed.NotFoundError:
        return {"status": "error", "message": f"{name} is not followed"}

    if episode in followed.episodes:
        return {
            "status": "success",
            "message": f"episode {episode} of {name} is already marked as seen",
            "episode": episode,
            **_seen_payload(followed, episode=episode),
        }

    followed.episodes.add(episode)
    followed.save()

    with Session.begin() as session:
        session.execute(
            sa.update(Download)
            .where(Download.bangumi_name == name, Download.episode == episode)
            .values(status=Download.STATUS_DOWNLOADED, task_id=None)
        )

    return {
        "status": "success",
        "message": f"Marked episode {episode} of {name} as seen",
        "episode": episode,
        **_seen_payload(followed, episode=episode),
    }


def _cover_needs_download(cover_url: str) -> bool:
    if not cover_url or _is_invalid_cover(cover_url):
        return False

    _, file_path = convert_cover_url_to_path(cover_url)
    return not (os.path.isfile(file_path) and filetype.is_image(file_path))


def _is_invalid_cover(cover_url: str) -> bool:
    return cover_url.endswith("/subscribed-badge.svg") or cover_url.endswith("subscribed-badge.svg")


def _refresh_missing_followed_covers() -> None:
    missing_cover = [
        (followed, bangumi)
        for followed, bangumi in Followed.get_all_followed()
        if not bangumi.cover or _is_invalid_cover(bangumi.cover)
    ]
    if not missing_cover:
        return

    print_info(f"Refreshing missing covers ({len(missing_cover)} bangumi) ...")
    for index, (followed, bangumi) in enumerate(missing_cover, start=1):
        print_info(f"Refreshing cover {index}/{len(missing_cover)}: {bangumi.name}")

        try:
            info = website.fetch_single_bangumi(
                bangumi.id,
                subtitle_list=followed.subtitle,
                max_page=cfg.max_path,
            )
        except Exception as e:
            print_warning(f"Failed to refresh cover for {bangumi.name}: {e}")
            logger.warning("Failed to refresh cover for {}: {}", bangumi.name, e)
            continue

        if info is not None and info.cover:
            website.save_bangumi(info)


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
        _refresh_missing_followed_covers()
        weekly_list = Bangumi.get_updating_bangumi()

        # download cover to local
        cover_to_be_download = [url for url in cover if url]
        for daily_bangumi in weekly_list.values():
            for bangumi in daily_bangumi:
                if _cover_needs_download(bangumi["cover"]):
                    cover_to_be_download.append(bangumi["cover"])

        cover_to_be_download = list(dict.fromkeys(cover_to_be_download))
        if cover_to_be_download:
            print_info(f"Updating cover ({len(cover_to_be_download)} files) ...")
            download_cover(cover_to_be_download)
        else:
            print_info("Cover is up to date.")

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

    if download:
        download_previous_failed_downloads()

    if not names:
        updated_bangumi_obj = sorted([x[0] for x in Followed.get_all_followed()], key=attrgetter("bangumi_name"))
    else:
        updated_bangumi_obj = []
        for n in names:
            try:
                f = Followed.get(Followed.bangumi_name == n)
                updated_bangumi_obj.append(f)
            except Followed.NotFoundError:
                logger.warning("missing followed bangumi '{}'", n)

    runner = ScriptRunner()

    for script, all_episode_data in runner.run():
        if not download:
            script.episodes.update([x.episode for x in all_episode_data])
            script.updated_time = now
            script.save()
        else:
            download_episodes(all_episode_data, script)

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
            following.episodes.update({x.episode for x in all_episode_data})
            following.save()
        else:
            download_episodes(all_episode_data, following)


def download_previous_failed_downloads() -> None:
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


def download_episodes(all_episode_data: List[Episode], following: Union[Followed, Scripts]) -> None:
    groups: Dict[int, List[Episode]] = {
        key: list(value) for key, value in itertools.groupby(all_episode_data, lambda x: x.episode)
    }

    updated = False

    for ep, episodes in sorted(groups.items()):
        if ep <= 0:
            continue
        if ep in following.episodes:
            continue

        print_success(f"{following.bangumi_name} updated, episode: {ep:d}")

        if episodes:
            for e in episodes:
                if download_episode(e):
                    updated = True
                    following.episodes.add(ep)  # type: ignore
                    break

    if updated:
        following.status = Followed.STATUS_UPDATED
        following.updated_time = int(time.time())
        following.save()
