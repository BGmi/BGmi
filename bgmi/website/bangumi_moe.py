import datetime
import os
import time
from typing import Any, Dict, List, Optional

import requests

from bgmi.config import BANGUMI_MOE_URL, LANG
from bgmi.lib.constants import BANGUMI_UPDATE_TIME
from bgmi.utils import bug_report, print_error, print_info, print_warning
from bgmi.website.base import BaseWebsite
from bgmi.website.model import Episode, SubtitleGroup, WebsiteBangumi

# tag of bangumi on bangumi.moe
BANGUMI_TAG = "549ef207fe682f7549f1ea90"

__split = "/" if not BANGUMI_MOE_URL.endswith("/") else ""
FETCH_URL = f"{BANGUMI_MOE_URL}{__split}api/bangumi/current"
TEAM_URL = f"{BANGUMI_MOE_URL}{__split}api/team/working"
NAME_URL = f"{BANGUMI_MOE_URL}{__split}api/tag/fetch"
DETAIL_URL = f"{BANGUMI_MOE_URL}{__split}api/torrent/search"
SEARCH_URL = f"{BANGUMI_MOE_URL}{__split}api/v2/torrent/search"
TORRENT_URL = f"{BANGUMI_MOE_URL}{__split}download/torrent/"
COVER_URL = "https://bangumi.moe/"


def get_response(url, method="GET", **kwargs):
    if os.environ.get("DEBUG"):  # pragma: no cover
        print_info(f"Request URL: {url}")
    try:
        r = requests.request(method.lower(), url, **kwargs)
        if os.environ.get("DEBUG"):  # pragma: no cover
            print(r.text)
        return r.json()
    except requests.ConnectionError:
        print_error("error: failed to establish a new connection")
    except ValueError:
        print_error(
            "error: server returned data maybe not be json,"
            " please create a issue at https://github.com/BGmi/BGmi/issues"
        )


def process_name(data):
    lang = "zh_cn" if LANG not in ("zh_cn", "zh_tw", "ja", "en") else LANG
    return {i["_id"]: i["locale"][lang] for i in data}


def process_subtitle(data):
    """get subtitle group name from links"""
    result = {}
    for s in data:
        result[s["tag_id"]] = s["name"]
    return result


def parser_bangumi(data):
    """match weekly bangumi list from data"""

    ids = list(map(lambda b: b["tag_id"], data))
    subtitle = get_response(TEAM_URL, "POST", json={"tag_ids": ids})
    name = process_name(get_response(NAME_URL, "POST", json={"_ids": ids}))

    weekly_list = []
    bangumi_update_time_known = BANGUMI_UPDATE_TIME[:-1]
    for bangumi_item in data:
        subtitle_of_bangumi = process_subtitle(subtitle.get(bangumi_item["tag_id"], []))
        item = {
            "status": 0,
            "subtitle_group": [
                SubtitleGroup(id=id, name=name)
                for id, name in subtitle_of_bangumi.items()
            ],
            "name": name[bangumi_item["tag_id"]],
            "keyword": bangumi_item["tag_id"],
            "update_time": bangumi_update_time_known[bangumi_item["showOn"] - 1],
            "cover": COVER_URL + bangumi_item["cover"],
        }

        if item["name"] is None:
            item["name"] = bangumi_item["name"]

        weekly_list.append(item)

    if not weekly_list:
        bug_report()
    return weekly_list


class BangumiMoe(BaseWebsite):
    def fetch_episode_of_bangumi(
        self,
        bangumi_id: str,
        max_page: int,
        subtitle_list: Optional[List[str]] = None,
    ) -> List[Episode]:
        response_data = []
        ret = []
        if subtitle_list:
            for subtitle_id in subtitle_list:
                data = {
                    "tag_id": [bangumi_id, subtitle_id, BANGUMI_TAG]
                }  # type: Dict[str, Any]
                response = get_response(DETAIL_URL, "POST", json=data)
                response_data.extend(response["torrents"])
        else:
            for i in range(max_page):
                if max_page > 1:
                    print_info("Fetch page {} ...".format(i + 1))
                data = {
                    "tag_id": [bangumi_id, BANGUMI_TAG],
                    "p": i + 1,
                }
                response = get_response(DETAIL_URL, "POST", json=data)
                if response:
                    response_data.extend(response["torrents"])
        for index, bangumi in enumerate(response_data):
            ret.append(
                Episode(
                    download=TORRENT_URL + bangumi["_id"] + "/download.torrent",
                    subtitle_group=bangumi["team_id"],
                    title=bangumi["title"],
                    episode=self.parse_episode(bangumi["title"]),
                    time=int(
                        datetime.datetime.strptime(
                            bangumi["publish_time"].split(".")[0], "%Y-%m-%dT%H:%M:%S"
                        ).timestamp()
                    ),
                )
            )

            if os.environ.get("DEBUG"):
                print(ret[index].download)

        return ret

    def fetch_bangumi_calendar(self) -> List[WebsiteBangumi]:
        response = get_response(FETCH_URL)
        if not response:
            return []
        bangumi_result = parser_bangumi(response)
        return [WebsiteBangumi(**x) for x in bangumi_result]

    def search_by_keyword(self, keyword: str, count: Optional[int] = None) -> list:
        if not count:
            count = 3

        rows = []
        result = []

        for i in range(count):
            data = get_response(SEARCH_URL, "POST", json={"query": keyword, "p": i + 1})
            if "torrents" not in data:
                print_warning("No torrents in response data, please re-run")
                return []
            rows.extend(data["torrents"])

        for info in rows:
            result.append(
                Episode(
                    download=TORRENT_URL + info["_id"] + "/download.torrent",
                    name=keyword,
                    subtitle_group=info["team_id"],
                    title=info["title"],
                    episode=self.parse_episode(info["title"]),
                    time=int(
                        time.mktime(
                            datetime.datetime.strptime(
                                info["publish_time"].split(".")[0], "%Y-%m-%dT%H:%M:%S"
                            ).timetuple()
                        )
                    ),
                )
            )

        # Avoid bangumi collection. It's ok but it will waste your traffic and bandwidth.
        result = result[::-1]
        return result
