import imghdr
import os.path
import time
from operator import itemgetter
from typing import Any, Dict, List, Optional, Union

import requests.exceptions

from bgmi.config import MAX_PAGE, write_config
from bgmi.lib.constants import BANGUMI_UPDATE_TIME, SUPPORT_WEBSITE
from bgmi.lib.download import Episode, download_prepare
from bgmi.lib.fetch import website
from bgmi.lib.models import (
    FOLLOWED_STATUS,
    STATUS_DELETED,
    STATUS_FOLLOWED,
    STATUS_NOT_DOWNLOAD,
    STATUS_UPDATED,
    Bangumi,
    DoesNotExist,
    Download,
    Filter,
    Followed,
    Subtitle,
    model_to_dict,
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


def add(name: str, episode: int = None) -> ControllerResult:
    """
    ret.name :str
    """
    # action add
    # add bangumi by a list of bangumi name
    logger.debug(f"add name: {name} episode: {episode}")
    if not Bangumi.get_updating_bangumi():
        website.fetch(save=True, group_by_weekday=False)

    try:
        bangumi_obj = Bangumi.fuzzy_get(name=name)
    except Bangumi.DoesNotExist:
        result = {
            "status": "error",
            "message": f"{name} not found, please check the name",
        }
        return result
    followed_obj, this_obj_created = Followed.get_or_create(
        bangumi_name=bangumi_obj.name, defaults={"status": STATUS_FOLLOWED}
    )
    if not this_obj_created:
        if followed_obj.status == STATUS_FOLLOWED:
            result = {
                "status": "warning",
                "message": f"{bangumi_obj.name} already followed",
            }
            return result
        else:
            followed_obj.status = STATUS_FOLLOWED
            followed_obj.save()

    Filter.get_or_create(bangumi_name=name)

    max_episode, _ = website.get_maximum_episode(bangumi_obj, max_page=int(MAX_PAGE))
    followed_obj.episode = max_episode if episode is None else episode

    followed_obj.save()
    result = {
        "status": "success",
        "message": f"{bangumi_obj.name} has been followed",
    }
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
    except Bangumi.DoesNotExist:
        result["status"] = "error"
        result["message"] = f"Bangumi {name} does not exist."
        return result

    try:
        Followed.get(bangumi_name=bangumi_obj.name)
    except Followed.DoesNotExist:
        result["status"] = "error"
        result[
            "message"
        ] = "Bangumi {name} has not subscribed, try 'bgmi add \"{name}\"'.".format(
            name=bangumi_obj.name
        )
        return result

    followed_filter_obj, is_this_obj_created = Filter.get_or_create(bangumi_name=name)

    if is_this_obj_created:
        followed_filter_obj.save()

    if subtitle is not None:
        _subtitle = [s.strip() for s in subtitle.split(",")]
        _subtitle = [s["id"] for s in Subtitle.get_subtitle_by_name(_subtitle)]
        subtitle_list = [
            s.split(".")[0] for s in bangumi_obj.subtitle_group.split(", ") if "." in s
        ]
        subtitle_list.extend(bangumi_obj.subtitle_group.split(", "))
        followed_filter_obj.subtitle = ", ".join(
            filter(lambda s: s in subtitle_list, _subtitle)
        )

    if include is not None:
        followed_filter_obj.include = include

    if exclude is not None:
        followed_filter_obj.exclude = exclude

    if regex is not None:
        followed_filter_obj.regex = regex

    followed_filter_obj.save()
    subtitle_list = [
        s["name"]
        for s in Subtitle.get_subtitle_by_id(bangumi_obj.subtitle_group.split(", "))
    ]

    result["data"] = {
        "name": name,
        "subtitle_group": subtitle_list,
        "followed": [
            s["name"]
            for s in Subtitle.get_subtitle_by_id(
                followed_filter_obj.subtitle.split(", ")
            )
        ]
        if followed_filter_obj.subtitle
        else [],
        "include": followed_filter_obj.include,
        "exclude": followed_filter_obj.exclude,
        "regex": followed_filter_obj.regex,
    }
    logger.debug(result)
    return result


def delete(
    name: str = "", clear_all: bool = False, batch: bool = False
) -> ControllerResult:
    """
    :param name:
    :param clear_all:
    :param batch:
    """
    # action delete
    # just delete subscribed bangumi or clear all the subscribed bangumi
    result = {}
    logger.debug(f"delete {name}")
    if clear_all:
        if Followed.delete_followed(batch=batch):
            result["status"] = "warning"
            result["message"] = "all subscriptions have been deleted"
        else:
            print_error("user canceled")
    elif name:
        try:
            followed = Followed.get(bangumi_name=name)
            followed.status = STATUS_DELETED
            followed.save()
            result["status"] = "warning"
            result["message"] = f"Bangumi {name} has been deleted"
        except Followed.DoesNotExist:
            result["status"] = "error"
            result["message"] = f"Bangumi {name} does not exist"
    else:
        result["status"] = "warning"
        result["message"] = "Nothing has been done."
    logger.debug(result)
    return result


def cal(
    force_update: bool = False, save: bool = False, cover: Optional[List[str]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    logger.debug(f"cal force_update: {force_update} save: {save}")

    weekly_list = Bangumi.get_updating_bangumi()
    if not weekly_list:
        print_warning("Warning: no bangumi schedule, fetching ...")
        force_update = True

    if force_update:
        print_info("Fetching bangumi info ...")
        website.fetch(save=save)

    weekly_list = Bangumi.get_updating_bangumi()

    if cover is not None:
        # download cover to local
        cover_to_be_download = cover
        for daily_bangumi in weekly_list.values():
            for bangumi in daily_bangumi:
                _, file_path = convert_cover_url_to_path(bangumi["cover"])

                if not (os.path.exists(file_path) and bool(imghdr.what(file_path))):
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
            subtitle_group = list(
                map(
                    lambda x: {"name": x["name"], "id": x["id"]},
                    Subtitle.get_subtitle_by_id(
                        bangumi["subtitle_group"].split(", " "")
                    ),
                )
            )

            r[day][index]["subtitle_group"] = subtitle_group
    logger.debug(r)
    return r


def download(name: str, title: str, episode: int, download_url: str) -> None:
    download_prepare(
        [Episode(name=name, title=title, episode=episode, download=download_url)]
    )


def mark(name: str, episode: int) -> ControllerResult:
    """

    :param name: name of the bangumi you want to mark
    :param episode: bangumi episode you want to mark
    """
    result = {}
    try:
        followed_obj = Followed.get(bangumi_name=name)
    except Followed.DoesNotExist:
        runner = ScriptRunner()
        followed_obj = runner.get_model(name)  # type: ignore
        if not followed_obj:
            result["status"] = "error"
            result["message"] = f"Subscribe or Script <{name}> does not exist."
            return result

    if episode is not None:
        followed_obj.episode = episode
        followed_obj.save()
        result["status"] = "success"
        result["message"] = f"{name} has been mark as episode: {episode}"
    else:  # episode is None
        result["status"] = "info"
        result["message"] = f"{name}, episode: {followed_obj.episode}"
    return result


def search(
    keyword: str,
    count: Union[str, int] = MAX_PAGE,
    regex: str = None,
    dupe: bool = False,
    min_episode: int = None,
    max_episode: int = None,
) -> ControllerResult:
    try:
        count = int(count)
    except (TypeError, ValueError):
        count = 3
    try:
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
        write_config("DATA_SOURCE", data_source)
        print_success("data source switch succeeds")
        result["status"] = "success"
        result[
            "message"
        ] = f"you have successfully change your data source to {data_source}"
    else:
        result["status"] = "error"
        result[
            "message"
        ] = "please check your input. data source should be one of {}".format(
            [x["id"] for x in SUPPORT_WEBSITE]
        )
    return result


def config(name: Optional[str] = None, value: Optional[str] = None) -> ControllerResult:
    if name == "DATA_SOURCE":
        error_message = (
            "you can't change data source in this way. "
            "please use `bgmi source ${data source}` in cli"
        )
        result = {
            "status": "error",
            "message": error_message,
            "data": write_config()["data"],
        }
        return result
    r = write_config(name, value)
    if name == "ADMIN_TOKEN":
        r["message"] = "you need to restart your bgmi_http to make new token work"
    return r


def update(
    name: List[str], download: Any = None, not_ignore: bool = False
) -> ControllerResult:
    logger.debug(f"updating bangumi info with args: download: {download}")
    result: Dict[str, Any] = {
        "status": "info",
        "message": "",
        "data": {"updated": [], "downloaded": []},
    }

    ignore = not bool(not_ignore)
    print_info("marking bangumi status ...")
    now = int(time.time())

    for i in Followed.get_all_followed():
        if i["updated_time"] and int(i["updated_time"] + 60 * 60 * 24) < now:
            followed_obj = Followed.get(bangumi_name=i["bangumi_name"])
            followed_obj.status = STATUS_FOLLOWED
            followed_obj.save()

    for script in ScriptRunner().scripts:
        obj = script.Model().obj
        if obj.updated_time and int(obj.updated_time + 60 * 60 * 24) < now:
            obj.status = STATUS_FOLLOWED
            obj.save()

    print_info("updating subscriptions ...")
    download_queue = []

    if download:
        if not name:
            print_warning("No specified bangumi, ignore `--download` option")
        if len(name) > 1:
            print_warning("Multiple specified bangumi, ignore `--download` option")

    if not name:
        updated_bangumi_obj = Followed.get_all_followed()
    else:
        updated_bangumi_obj = []
        for n in name:
            try:
                f = Followed.get(bangumi_name=n)
                f = model_to_dict(f)
                updated_bangumi_obj.append(f)
            except DoesNotExist:
                pass

    runner = ScriptRunner()
    script_download_queue = runner.run()

    for subscribe in updated_bangumi_obj:
        print_info(f"fetching {subscribe['bangumi_name']} ...")
        try:
            bangumi_obj = Bangumi.get(name=subscribe["bangumi_name"])
        except Bangumi.DoesNotExist:
            print_error(
                "Bangumi<{}> does not exists.".format(subscribe["bangumi_name"]),
                exit_=False,
            )
            continue
        try:
            followed_obj = Followed.get(bangumi_name=subscribe["bangumi_name"])
        except Followed.DoesNotExist:
            print_error(
                "Bangumi<{}> is not followed.".format(subscribe["bangumi_name"]),
                exit_=False,
            )
            continue

        try:
            episode, all_episode_data = website.get_maximum_episode(
                bangumi=bangumi_obj, ignore_old_row=ignore, max_page=int(MAX_PAGE)
            )
        except requests.exceptions.ConnectionError as e:
            print_warning(f"error {e} to fetch {bangumi_obj.name}, skip")
            continue

        if (episode > subscribe["episode"]) or (len(name) == 1 and download):
            if len(name) == 1 and download:
                episode_range = download
            else:
                episode_range = range(subscribe["episode"] + 1, episode + 1)
                print_success(
                    f"{subscribe['bangumi_name']} updated, episode: {episode:d}"
                )
                followed_obj.episode = episode
                followed_obj.status = STATUS_UPDATED
                followed_obj.updated_time = int(time.time())
                followed_obj.save()
                result["data"]["updated"].append(
                    {"bangumi": subscribe["bangumi_name"], "episode": episode}
                )

            for i in episode_range:
                for epi in all_episode_data:
                    if epi.episode == i:
                        download_queue.append(epi)
                        break

    if download is not None:
        result["data"]["downloaded"] = download_queue
        download_prepare(download_queue)
        download_prepare(script_download_queue)
        print_info("Re-downloading ...")
        download_prepare(
            [
                Episode(
                    **{
                        key: value
                        for key, value in x.items()
                        if key not in ["id", "status"]
                    }
                )
                for x in Download.get_all_downloads(status=STATUS_NOT_DOWNLOAD)
            ]
        )

    return result


def status_(name: str, status: int = STATUS_DELETED) -> ControllerResult:
    result = {"status": "success", "message": ""}

    if (status not in FOLLOWED_STATUS) or (not status):
        result["status"] = "error"
        result["message"] = f"Invalid status: {status}"
        return result

    status = int(status)
    try:
        followed_obj = Followed.get(bangumi_name=name)
    except Followed.DoesNotExist:
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
                if (
                    bangumi["status"] in (STATUS_UPDATED, STATUS_FOLLOWED)
                    and "episode" in bangumi
                ):
                    bangumi["name"] = f"{bangumi['name']}({bangumi['episode']:d})"
                if j > 0:
                    result["message"] += " " * 5
                f = [x["name"] for x in bangumi["subtitle_group"]]
                result["message"] += "{}: {}\n".format(
                    bangumi["name"], ", ".join(f) if f else "<None>"
                )

    return result
