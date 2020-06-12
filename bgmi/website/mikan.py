import os
import time
from collections import defaultdict
from functools import reduce
from multiprocessing.pool import ThreadPool
from typing import List

import bs4
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

from bgmi.config import MAX_PAGE, TMP_PATH
from bgmi.website.base import BaseWebsite

_DEBUG = "mikan" in os.environ.get("DEBUG", "").lower()
_DUMP = _DEBUG and "dump" in os.environ.get("DEBUG", "").lower()

_session = requests.Session()
_session.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504]
        )
    ),
)

week = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
server_root = "https://mikanani.me/"


Cn_week_map = {
    "星期日": "Sun",
    "星期一": "Mon",
    "星期二": "Tue",
    "星期三": "Wed",
    "星期四": "Thu",
    "星期五": "Fri",
    "星期六": "Sat",
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
            yield d


def parser_day_bangumi(soup):
    """

    :param soup:
    :type soup: bs4.Tag
    :return: list
    :rtype: list[dict]
    """
    li = []
    for soup in soup.find_all("li"):
        url = soup.select_one("a")
        span = soup.find("span")
        if url:
            name = url["title"]
            url = url["href"]
            assert isinstance(url, str)
            bangumi_id = url.split("/")[-1]
            soup.find("li",)
            li.append({"name": name, "keyword": bangumi_id, "cover": span["data-src"]})
    return li


def get_text(url, params=None):
    if _DEBUG:  # pragma: no cover
        print(url)
    res = _session.get(url, params=params)
    res.raise_for_status()
    r = res.text
    if _DEBUG:  # pragma: no cover
        print(r)
    return r


class Mikanani(BaseWebsite):
    cover_url = server_root[:-1]

    def parse_bangumi_details_page(self, r):

        subtitle_groups = defaultdict(dict)

        soup = BeautifulSoup(r, "html.parser")

        # info
        bangumi_info = {"status": 0}
        left_container = soup.select_one("div.pull-left.leftbar-container")
        title = left_container.find("p", class_="bangumi-title")
        day = title.find_next_sibling("p", class_="bangumi-info")
        bangumi_info["update_time"] = Cn_week_map[day.text[-3:]]

        ######
        soup = BeautifulSoup(r, "html.parser")
        container = soup.find("div", class_="central-container")
        episode_container_list = {}
        for index, tag in enumerate(container.contents):
            if not hasattr(tag, "attrs"):
                continue
            subtitle_id = tag.attrs.get("id", False)
            if subtitle_id:
                episode_container_list[
                    tag.attrs.get("id", None)
                ] = tag.find_next_sibling("table")

        for subtitle_id, container in episode_container_list.items():
            subtitle_groups[str(subtitle_id)]["episode"] = list()
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
        bangumi_info["subtitle_group"] = list(subtitle_groups.keys())
        nr = list()
        dv = soup.find("div", class_="leftbar-nav")
        li_list = dv.ul.find_all("li")
        for li in li_list:
            a = li.find("a")
            subtitle = {
                "id": a.attrs["data-anchor"][1:],
                "name": a.text,
            }
            nr.append(subtitle)

        bangumi_info["subtitle_groups"] = nr
        return bangumi_info

    def search_by_keyword(self, keyword, count=None):
        """
        return a list of dict with at least 4 key: download, name, title, episode
        example:
        ```
            [
                {
                    'name':"路人女主的养成方法",
                    'download': 'magnet:?xt=urn:btih:what ever',
                    'title': "[澄空学园] 路人女主的养成方法 第12话 MP4 720p  完",
                    'episode': 12
                },
            ]
        ```
        :param keyword: search key word
        :type keyword: str
        :param count: how many page to fetch from website
        :type count: int

        :return: list of episode search result
        :rtype: list[dict]
        """

        result = []
        r = get_text(server_root + "Home/Search", params={"searchstr": keyword})
        s = BeautifulSoup(r, "html.parser")
        td_list = s.find_all("tr", attrs={"class": "js-search-results-row"})
        for tr in td_list:
            title = tr.find("a", class_="magnet-link-wrap").text
            time_string = tr.find_all("td")[2].string
            result.append(
                {
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
            # print(result)
        return result

    def fetch_episode_of_bangumi(
        self, bangumi_id, subtitle_list=None, max_page=MAX_PAGE
    ):
        """
        get all episode by bangumi id
        example
        ```
            [
                {
                    "download": "magnet:?xt=urn:btih:e43b3b6b536a1199e112d3c7ff15cab82c",
                    "subtitle_group": "58a9c1c9f5dc363606ab42ec",
                    "title": "【喵萌奶茶屋】★七月新番★[来自深渊/Made in Abyss][07][GB][720P]",
                    "episode": 0,
                    "time": 1503301292
                },
            ]
        ```

        :param bangumi_id: bangumi_id
        :param subtitle_list: list of subtitle group
        :type subtitle_list: list
        :param max_page: how many page you want to crawl if there is no subtitle list
        :type max_page: int
        :return: list of bangumi
        :rtype: list[dict]
        """

        result = []

        r = get_text(server_root + "Home/Bangumi/{}".format(bangumi_id))

        soup = BeautifulSoup(r, "html.parser")
        # name = soup.find('p', class_='bangumi-title').text
        container = soup.find("div", class_="central-container")  # type:bs4.Tag
        episode_container_list = {}
        for index, tag in enumerate(container.contents):
            if not hasattr(tag, "attrs"):
                continue
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
            for tr in container.find_all("tr")[1:]:
                title = tr.find("a", class_="magnet-link-wrap").text
                time_string = tr.find_all("td")[2].string
                result.append(
                    {
                        "download": server_root[:-1]
                        + tr.find_all("td")[-1].find("a",).attrs.get("href", ""),
                        "subtitle_group": str(subtitle_id),
                        "title": title,
                        "episode": self.parse_episode(title),
                        "time": int(
                            time.mktime(time.strptime(time_string, "%Y/%m/%d %H:%M"))
                        ),
                    }
                )

        return result

    def fetch_bangumi_calendar_and_subtitle_group(self):
        """
        return a list of all bangumi and a list of all subtitle group

        list of bangumi dict:
        update time should be one of ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        example:
        ```
            [
                {
                    "status": 0,
                    "subtitle_group": [
                        "123",
                        "456"
                    ],
                    "name": "名侦探柯南",
                    "keyword": "1234", #bangumi id
                    "update_time": "Sat",
                    "cover": "data/images/cover1.jpg"
                },
            ]
        ```

        list of subtitle group dict:
        example:
        ```
            [
                {
                    'id': '233',
                    'name': 'bgmi字幕组'
                }
            ]
        ```


        :return: list of bangumi, list of subtitile group
        :rtype: (list[dict], list[dict])
        """
        subtitle_result = []  # type: List[List[dict]]
        bangumi_list = []
        for day in get_weekly_bangumi():
            for obj in parser_day_bangumi(day):
                bangumi_list.append(obj)

        def wrapper(info):
            html = get_text(server_root + "Home/Bangumi/{}".format(info["keyword"]))
            try:
                info.update(self.parse_bangumi_details_page(html))
                return info
            except AttributeError:
                if _DUMP:
                    try:
                        os.makedirs(os.path.join(TMP_PATH, "mikan"))
                    except OSError:
                        pass
                    with open(
                        os.path.join(TMP_PATH, "mikan", info["keyword"] + ".html"),
                        "w",
                        encoding="utf-8",
                    ) as fd:
                        fd.write(html)

        with ThreadPool() as p:
            bangumi_result = [x for x in p.map(wrapper, [x for x in bangumi_list]) if x]

        [subtitle_result.extend(x["subtitle_groups"]) for x in bangumi_result]

        def f(x, y):
            return x if y in x else x + [y]

        subtitle_result = reduce(f, [[]] + subtitle_result)
        subtitle_result.sort(key=lambda x: int(x["id"]))

        return bangumi_result, subtitle_result
