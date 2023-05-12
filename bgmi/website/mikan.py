import datetime
import os
import time
from collections import defaultdict
from typing import List, Optional
from xml.etree import ElementTree

import bs4
from bs4 import BeautifulSoup
from strsimpy.normalized_levenshtein import NormalizedLevenshtein

from bgmi.config import cfg
from bgmi.session import session as requests
from bgmi.utils import parse_episode, print_info
from bgmi.website.base import BaseWebsite
from bgmi.website.model import Episode, SubtitleGroup, WebsiteBangumi

server_root = f"{cfg.mikan_url.rstrip('/')}/"
login_url = f"{server_root}Account/Login"

_COVER_URL = server_root[:-1]

# Example: /Home/ExpandEpisodeTable?bangumiId=2242&subtitleGroupId=34&take=65
bangumi_episode_expand_api = f"{server_root}Home/ExpandEpisodeTable"

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
        d = soup.find("div", attrs={"class": "sk-bangumi", "data-dayofweek": str(day_of_week)})
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
                episode_container_list[tag.attrs.get("id", None)] = tag.find_next_sibling("table")
        else:
            if subtitle_id:
                episode_container_list[tag.attrs.get("id", None)] = tag.find_next_sibling("table")

    for subtitle_id, container in episode_container_list.items():
        _container = container
        if subtitle_id in expand_subtitle_map:
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
                    download=tr.find("a", class_="magnet-link").attrs["data-clipboard-text"],
                    subtitle_group=str(subtitle_id),
                    title=title,
                    episode=parse_episode(title),
                    time=int(time.mktime(time.strptime(time_string, "%Y/%m/%d %H:%M"))),
                )
            )

    return result


def parser_day_bangumi(soup) -> List[WebsiteBangumi]:
    """

    :param soup:
    :type soup: bs4.Tag
    """
    li = []
    for s in soup.find_all("li"):
        url = s.select_one("a")
        span = s.find("span")
        if url:
            name = url["title"]
            url = url["href"]
            bangumi_id = url.split("/")[-1]
            s.find("li")
            li.append(WebsiteBangumi(name=name, keyword=bangumi_id, cover=_COVER_URL + span["data-src"]))
    return li


def mikan_login():
    r = requests.get(login_url)
    soup = BeautifulSoup(r.text, "html.parser")
    token = soup.find("input", attrs={"name": "__RequestVerificationToken"})["value"]

    if os.environ.get("DEBUG", False):  # pragma: no cover
        print(login_url)

    r = requests.post(
        login_url,
        data={
            "UserName": cfg.mikan_username,
            "Password": cfg.mikan_password,
            "__RequestVerificationToken": token,
        },
        headers={"Referer": server_root},
        allow_redirects=False,
    )

    if "&#x767B;&#x5F55;&#x5931;&#x8D25;&#xFF0C;&#x8BF7;&#x91CD;&#x8BD5;" in r.text:  # 实际为 "登录失败，请重试"
        raise ValueError("mikan login failed with wrong username or password")


def get_text(url, params=None):
    if os.environ.get("DEBUG", False):  # pragma: no cover
        print(url, params)

    if not cfg.mikan_username or not cfg.mikan_password:
        return requests.get(url, params=params).text

    for _ in range(2):
        r = requests.get(url, params=params)
        if r.headers.get("content-type").startswith("text/html"):
            if "退出" in r.text:
                return r.text
            else:
                mikan_login()
        else:
            return r.text

    raise ValueError("mikan login failed")


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
                episode_container_list[tag.attrs.get("id")] = tag.find_next_sibling("table")

        for subtitle_id, container in episode_container_list.items():
            subtitle_groups[str(subtitle_id)]["episode"] = []
            for tr in container.find_all("tr")[1:]:
                title = tr.find("a", class_="magnet-link-wrap").text
                time_string = tr.find_all("td")[2].string
                subtitle_groups[str(subtitle_id)]["episode"].append(
                    {
                        "download": tr.find("a", class_="magnet-link").attrs["data-clipboard-text"],
                        "subtitle_group": str(subtitle_id),
                        "title": title,
                        "episode": self.parse_episode(title),
                        "time": int(time.mktime(time.strptime(time_string, "%Y/%m/%d %H:%M"))),
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

    def search_by_tag(self, tag: str, subtitle: Optional[str] = None, count: Optional[int] = None) -> List[Episode]:
        r = get_text(server_root + "Home/Search", params={"searchstr": tag})
        s = BeautifulSoup(r, "html.parser")
        animate = s.find_all("div", attrs={"class": "an-info-group"})[0]
        animate_name = animate.text.strip()
        animate_link = animate.parent.parent.attrs["href"]
        animate_id = animate_link.split("/")[-1]
        print_info(f"Matched animate: {animate_name} ({animate_id})")
        animate_link = animate_link.lstrip("/")

        r = get_text(server_root + animate_link)
        s = BeautifulSoup(r, "html.parser")

        lowest_distance = 1.0
        best_sim_match_group = None

        normalized_levenshtein = NormalizedLevenshtein()

        subgroup_list = s.find_all("div", attrs={"class": "subgroup-text"})
        for subgroup in subgroup_list:
            subgroup_names = []
            subgroup_links = []
            sub_info = {}

            for href_ele in subgroup.find_all("a", href=True):
                link = href_ele["href"]

                subgroup_link_prefix = "/Home/PublishGroup/"
                rss_link_prefix = "/RSS/Bangumi"
                if link:
                    if link.startswith(subgroup_link_prefix):
                        subgroup_names.append(href_ele.text)
                        subgroup_links.append(link[len(subgroup_link_prefix) :])

                    if link.startswith(rss_link_prefix):
                        req: str = link[len(rss_link_prefix) + 1 :]
                        for r in req.split("&"):
                            key, val = r.split("=", maxsplit=1)
                            sub_info[key] = val
            if not subgroup_names:
                continue

            if subtitle:
                cmp_text = " ".join(subgroup_names)
                sim_distance = normalized_levenshtein.distance(cmp_text, subtitle)
                if sim_distance < lowest_distance:
                    lowest_distance = sim_distance
                    best_sim_match_group = (subgroup, subgroup_names, subgroup_links, sub_info)
            else:
                best_sim_match_group = (subgroup, subgroup_names, subgroup_links, sub_info)
                break

        if not best_sim_match_group:
            return []
        subgroup, subgroup_names, subgroup_links, sub_info = best_sim_match_group
        bangumiId, subgroupid = sub_info["bangumiId"], sub_info["subgroupid"]
        rss_url = f"{server_root}RSS/Bangumi?bangumiId={bangumiId}&subgroupid={subgroupid}"

        subtitle_group = " ".join(subgroup_names)
        if subtitle:
            print_info(f"Matched subtitle: {subtitle_group} ({subgroupid})")
        else:
            print_info(f"Use first subtitle: {subtitle_group} ({subgroupid})")

        r = get_text(rss_url)
        rss_root = ElementTree.fromstring(r)

        result = []
        for item in rss_root[0].findall("item"):
            enclosure_el = item.find("enclosure")
            link = enclosure_el.attrib.get("url") if enclosure_el is not None else None
            title_el = item.find("title")
            title = title_el.text if title_el is not None else None

            xmlns = "{" + server_root + "0.1/}"
            torrent = item.find(f"{xmlns}torrent")
            pub_date_el = torrent.find(f"{xmlns}pubDate") if torrent is not None else None
            pub_date = pub_date_el.text if pub_date_el is not None else None

            if link and title and pub_date:
                pub_date = pub_date.split(".")[0]
                pub_date_ts = int(datetime.datetime.strptime(pub_date, "%Y-%m-%dT%H:%M:%S").timestamp())

                result.append(
                    Episode(
                        download=link,
                        name=animate_name,
                        title=title,
                        subtitle_group=subtitle_group,
                        episode=self.parse_episode(title),
                        time=pub_date_ts,
                    )
                )
        result = result[::-1]
        return result

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
                        "download": tr.find("a", class_="magnet-link").attrs.get("data-clipboard-text", ""),
                        "name": keyword,
                        "title": title,
                        "episode": self.parse_episode(title),
                        "time": int(time.mktime(time.strptime(time_string, "%Y/%m/%d %H:%M"))),
                    }
                )
            )
        return result

    def fetch_episode_of_bangumi(self, bangumi_id, max_page=cfg.max_path, subtitle_list=None):
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
