import time
from collections import defaultdict
from typing import List, Optional

import bs4
import requests
from bs4 import BeautifulSoup

from bgmi.config import MAX_PAGE
from bgmi.utils import parse_episode
from bgmi.website.base import BaseWebsite
from bgmi.website.model import Episode, SubtitleGroup, WebsiteBangumi

server_root = "https://mikanani.me/"

_COVER_URL = server_root[:-1]

# Example: /Home/ExpandEpisodeTable?bangumiId=2242&subtitleGroupId=34&take=65
bangumi_episode_expand_api = "https://mikanani.me/Home/ExpandEpisodeTable"

_CN_WEEK = {
    "星期日": "Sun",
    "星期一": "Mon",
    "星期二": "Tue",
    "星期三": "Wed",
    "星期四": "Thu",
    "星期五": "Fri",
    "星期六": "Sat",
    "OVA": "Unknown",
}

_DAY_OF_WEEK = {
    0: "星期日",
    1: "星期一",
    2: "星期二",
    3: "星期三",
    4: "星期四",
    5: "星期五",
    6: "星期六",
    8: "OVA",
}


def get_weekly_bangumi():
    """
    network
    """
    r = get_text(server_root)
    soup = bs4.BeautifulSoup(r, "html.parser")
    for day_of_week in [x for x in range(0, 9) if x != 7]:
        d = soup.find(
            "div", attrs={"class": "sk-bangumi", "data-dayofweek": str(day_of_week)}
        )
        if d:
            try:
                yield _CN_WEEK[_DAY_OF_WEEK[day_of_week]], d
            except KeyError:
                pass


def parse_episodes(content, bangumi_id, subtitle_list=None) -> List[Episode]:
    result = []
    soup = BeautifulSoup(content, "html.parser")
    container = soup.find("div", class_="central-container")  # type:bs4.Tag
    episode_container_list = {}
    expand_subtitle_map = {}
    for tag in container.contents:
        if not hasattr(tag, "attrs"):
            continue

        class_names = tag.attrs.get("class")
        if class_names is not None and "episode-expand" in class_names:
            expand_subtitle_map[tag.attrs.get("data-subtitlegroupid", None)] = True

        subtitle_id = tag.attrs.get("id", False)
        if subtitle_list:
            if subtitle_id in subtitle_list:
                episode_container_list[
                    tag.attrs.get("id", None)
                ] = tag.find_next_sibling("table")
        else:
            if subtitle_id:
                episode_container_list[
                    tag.attrs.get("id", None)
                ] = tag.find_next_sibling("table")

    for subtitle_id, container in episode_container_list.items():
        _container = container
        if subtitle_id in expand_subtitle_map.keys():
            expand_r = requests.get(
                bangumi_episode_expand_api,
                params={
                    "bangumiId": bangumi_id,
                    "subtitleGroupId": subtitle_id,
                    "take": 200,
                },
            ).text
            expand_soup = BeautifulSoup(expand_r, "html.parser")
            _container = expand_soup.find("table")

        for tr in _container.find_all("tr")[1:]:
            title = tr.find("a", class_="magnet-link-wrap").text
            time_string = tr.find_all("td")[2].string
            result.append(
                Episode(
                    **{
                        "download": server_root[:-1]
                        + tr.find_all("td")[-1].find("a").attrs.get("href", ""),
                        "subtitle_group": str(subtitle_id),
                        "title": title,
                        "episode": parse_episode(title),
                        "time": int(
                            time.mktime(time.strptime(time_string, "%Y/%m/%d %H:%M"))
                        ),
                    }
                )
            )

    return result


def parser_day_bangumi(soup) -> List[WebsiteBangumi]:
    """

    :param soup:
    :type soup: bs4.Tag
    """
    li = []
    for soup in soup.find_all("li"):
        url = soup.select_one("a")
        span = soup.find("span")
        if url:
            name = url["title"]
            url = url["href"]
            bangumi_id = url.split("/")[-1]
            soup.find("li")
            li.append(
                WebsiteBangumi(
                    name=name, keyword=bangumi_id, cover=_COVER_URL + span["data-src"]
                )
            )
    return li


def get_text(url, params=None):
    return requests.get(url, params=params).text


class Mikanani(BaseWebsite):
    def parse_bangumi_details_page(self, r):

        subtitle_groups = defaultdict(dict)

        soup = BeautifulSoup(r, "html.parser")

        # info
        bangumi_info = {"status": 0}
        left_container = soup.select_one("div.pull-left.leftbar-container")
        title = left_container.find("p", class_="bangumi-title")
        day = title.find_next_sibling("p", class_="bangumi-info")
        bangumi_info["name"] = title.text
        bangumi_info["update_time"] = _CN_WEEK[day.text[-3:]]

        ######
        soup = BeautifulSoup(r, "html.parser")
        container = soup.find("div", class_="central-container")
        episode_container_list = {}
        for tag in container.contents:
            if not hasattr(tag, "attrs"):
                continue
            subtitle_id = tag.attrs.get("id", False)
            if subtitle_id:
                episode_container_list[tag.attrs.get("id")] = tag.find_next_sibling(
                    "table"
                )

        for subtitle_id, container in episode_container_list.items():
            subtitle_groups[str(subtitle_id)]["episode"] = []
            for tr in container.find_all("tr")[1:]:
                title = tr.find("a", class_="magnet-link-wrap").text
                time_string = tr.find_all("td")[2].string
                subtitle_groups[str(subtitle_id)]["episode"].append(
                    {
                        "download": tr.find("a", class_="magnet-link").attrs.get(
                            "data-clipboard-text", ""
                        ),
                        "subtitle_group": str(subtitle_id),
                        "title": title,
                        "episode": self.parse_episode(title),
                        "time": int(
                            time.mktime(time.strptime(time_string, "%Y/%m/%d %H:%M"))
                        ),
                    }
                )

        ######
        nr = []
        dv = soup.find("div", class_="leftbar-nav")
        li_list = dv.ul.find_all("li")
        for li in li_list:
            a = li.find("a")
            subtitle = {
                "id": a.attrs["data-anchor"][1:],
                "name": a.text,
            }
            nr.append(subtitle)

        bangumi_info["subtitle_group"] = [SubtitleGroup(**x) for x in nr]
        return bangumi_info

    def search_by_keyword(self, keyword, count=None):
        result = []
        r = get_text(server_root + "Home/Search", params={"searchstr": keyword})
        s = BeautifulSoup(r, "html.parser")
        td_list = s.find_all("tr", attrs={"class": "js-search-results-row"})
        for tr in td_list:
            title = tr.find("a", class_="magnet-link-wrap").text
            time_string = tr.find_all("td")[2].string
            result.append(
                Episode(
                    **{
                        "download": tr.find("a", class_="magnet-link").attrs.get(
                            "data-clipboard-text", ""
                        ),
                        "name": keyword,
                        "title": title,
                        "episode": self.parse_episode(title),
                        "time": int(
                            time.mktime(time.strptime(time_string, "%Y/%m/%d %H:%M"))
                        ),
                    }
                )
            )
        return result

    def fetch_episode_of_bangumi(
        self, bangumi_id, subtitle_list=None, max_page=MAX_PAGE
    ):
        r = get_text(server_root + f"Home/Bangumi/{bangumi_id}")
        return parse_episodes(r, bangumi_id, subtitle_list)

    def fetch_bangumi_calendar(self) -> List[WebsiteBangumi]:
        bangumi_list = []
        for update_time, day in get_weekly_bangumi():
            for obj in parser_day_bangumi(day):
                obj.update_time = update_time
                obj.cover = obj.cover.split("?")[0]
                bangumi_list.append(obj)
        return bangumi_list

    def fetch_single_bangumi(
        self,
        bangumi_id: str,
        subtitle_list: Optional[List[str]] = None,
        max_page: int = 0,
    ) -> Optional[WebsiteBangumi]:
        html = get_text(server_root + f"Home/Bangumi/{bangumi_id}")
        info = self.parse_bangumi_details_page(html)
        return WebsiteBangumi(
            name=info["name"],
            keyword=bangumi_id,
            status=info["status"],
            update_time=info["update_time"],
            subtitle_group=info["subtitle_group"],
            episodes=parse_episodes(html, bangumi_id, subtitle_list),
        )
