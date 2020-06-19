import imghdr
import os
import re
import time
from collections import defaultdict
from itertools import chain
from typing import Any, Dict, List, Optional, Tuple, TypeVar

import attr

from bgmi.config import ENABLE_GLOBAL_FILTER, GLOBAL_FILTER, MAX_PAGE
from bgmi.lib.models import (
    STATUS_FOLLOWED,
    STATUS_UPDATED,
    STATUS_UPDATING,
    Bangumi,
    Filter,
    Subtitle,
)
from bgmi.utils import (
    convert_cover_url_to_path,
    download_cover,
    parse_episode,
    print_info,
    print_warning,
    test_connection,
)
from bgmi.website.model import WebsiteBangumi

T = TypeVar("T", bound=dict)


class BaseWebsite:
    parse_episode = staticmethod(parse_episode)

    @staticmethod
    def save_bangumi(data: WebsiteBangumi) -> None:
        """save bangumi to database"""
        b, obj_created = Bangumi.get_or_create(
            keyword=data.keyword, defaults=attr.asdict(data)
        )
        if not obj_created:
            should_save = False
            if data.cover and b.cover != data.cover:
                b.cover = data.cover
                should_save = True

            if data.update_time != "Unknown" and data.update_time != b.update_time:
                b.update_time = data.update_time
                should_save = True

            subtitle_group = Bangumi(subtitle_group=data.subtitle_group).subtitle_group

            if b.status != STATUS_UPDATING or b.subtitle_group != subtitle_group:
                b.status = STATUS_UPDATING
                b.subtitle_group = subtitle_group
                should_save = True

            if should_save:
                b.save()

        for subtitle_group in data.subtitle_group:
            (
                Subtitle.insert(
                    {
                        Subtitle.id: str(subtitle_group.id),
                        Subtitle.name: str(subtitle_group.name),
                    }
                ).on_conflict_replace()
            ).execute()

    def fetch(self, save: bool = False, group_by_weekday: bool = True) -> Any:
        bangumi_result = self.fetch_bangumi_calendar()
        if not bangumi_result:
            print("can't fetch anything from website")
            return []
        Bangumi.delete_all()
        if save:
            for bangumi in bangumi_result:
                self.save_bangumi(bangumi)

        if group_by_weekday:
            result_group_by_weekday = defaultdict(list)
            for bangumi in bangumi_result:
                result_group_by_weekday[bangumi.update_time.lower()].append(bangumi)
            return result_group_by_weekday
        return bangumi_result

    @staticmethod
    def followed_bangumi() -> Dict[str, list]:
        """

        :return: list of bangumi followed
        """
        weekly_list_followed = Bangumi.get_updating_bangumi(status=STATUS_FOLLOWED)
        weekly_list_updated = Bangumi.get_updating_bangumi(status=STATUS_UPDATED)
        weekly_list = defaultdict(list)
        for k, v in chain(weekly_list_followed.items(), weekly_list_updated.items()):
            weekly_list[k].extend(v)
        for bangumi_list in weekly_list.values():
            for bangumi in bangumi_list:
                bangumi["subtitle_group"] = [
                    {"name": x["name"], "id": x["id"]}
                    for x in Subtitle.get_subtitle_by_id(
                        bangumi["subtitle_group"].split(", ")
                    )
                ]
        return weekly_list

    def bangumi_calendar(
        self, save: bool = True, cover: Optional[List[str]] = None,
    ) -> Dict[str, List[WebsiteBangumi]]:
        """

        :param save: set true to enable save bangumi data to database
        :param cover: list of cover url (of scripts) want to download
        """
        weekly_list = self.fetch(save=save)  # type:  Dict[str, List[WebsiteBangumi]]

        if cover is not None:
            # download cover to local
            cover_to_be_download = cover
            for daily_bangumi in weekly_list.values():
                for bangumi in daily_bangumi:
                    _, file_path = convert_cover_url_to_path(bangumi.cover)

                    if not (os.path.exists(file_path) and bool(imghdr.what(file_path))):
                        cover_to_be_download.append(bangumi.cover)

            if cover_to_be_download:
                print_info("Updating cover ...")
                download_cover(cover_to_be_download)

        return weekly_list

    def get_maximum_episode(
        self,
        bangumi: Bangumi,
        subtitle: bool = True,
        ignore_old_row: bool = True,
        max_page: int = int(MAX_PAGE),
    ) -> Tuple[dict, list]:
        followed_filter_obj, _ = Filter.get_or_create(bangumi_name=bangumi.name)

        if followed_filter_obj and subtitle:
            subtitle_group = followed_filter_obj.subtitle
        else:
            subtitle_group = None

        if followed_filter_obj and subtitle:
            include = followed_filter_obj.include
        else:
            include = None

        if followed_filter_obj and subtitle:
            exclude = followed_filter_obj.exclude
        else:
            exclude = None

        if followed_filter_obj and subtitle:
            regex = followed_filter_obj.regex
        else:
            regex = None

        info = self.fetch_single_bangumi(
            bangumi.keyword, subtitle_list=subtitle_group, max_page=max_page
        )
        if info is not None:
            self.save_bangumi(info)

        data = [
            i
            for i in self.fetch_episode(
                _id=bangumi.keyword,
                name=bangumi.name,
                subtitle_group=subtitle_group,
                include=include,
                exclude=exclude,
                regex=regex,
                max_page=max_page,
            )
            if i["episode"] is not None
        ]

        if ignore_old_row:
            data = [
                row
                for row in data
                if row["time"] > int(time.time()) - 3600 * 24 * 30 * 3
            ]  # three month

        if data:
            b = max(data, key=lambda _i: _i["episode"])  # type: dict
            return b, data
        else:
            return {"episode": 0}, []

    def fetch_episode(
        self,
        _id: str,
        name: str = "",
        subtitle_group: str = None,
        include: str = None,
        exclude: str = None,
        regex: str = None,
        max_page: int = int(MAX_PAGE),
    ) -> List[dict]:
        result = []

        max_page = int(max_page)

        if subtitle_group and subtitle_group.split(", "):
            condition = subtitle_group.split(", ")
            response_data = self.fetch_episode_of_bangumi(
                bangumi_id=_id, subtitle_list=condition, max_page=max_page
            )
        else:
            response_data = self.fetch_episode_of_bangumi(
                bangumi_id=_id, max_page=max_page
            )

        for info in response_data:
            if "合集" not in info["title"]:
                info["name"] = name
                result.append(info)

        if include:
            include_list = list(map(lambda s: s.strip(), include.split(",")))
            result = list(
                filter(
                    lambda s: True
                    if all(map(lambda t: t in s["title"], include_list))
                    else False,
                    result,
                )
            )

        if exclude:
            exclude_list = list(map(lambda s: s.strip(), exclude.split(",")))
            result = list(
                filter(
                    lambda s: True
                    if all(map(lambda t: t not in s["title"], exclude_list))
                    else False,
                    result,
                )
            )

        result = self.filter_keyword(data=result, regex=regex)
        return result

    @staticmethod
    def remove_duplicated_bangumi(result: List[T]) -> List[T]:
        """

        :type result: list[dict]
        """
        ret = []
        episodes = list({i["episode"] for i in result})
        for i in result:
            if i["episode"] in episodes:
                ret.append(i)
                del episodes[episodes.index(i["episode"])]

        return ret

    @staticmethod
    def filter_keyword(data: List[T], regex: str = None) -> List[T]:
        """

        :type regex: str
        :param data: list of bangumi dict
        :type data: list[dict]
        """
        if regex:
            try:
                match = re.compile(regex)
                data = [s for s in data if match.findall(s["title"])]
            except re.error as e:
                if os.getenv("DEBUG"):  # pragma: no cover
                    import traceback

                    traceback.print_exc()
                    raise e
                return data

        if not ENABLE_GLOBAL_FILTER == "0":
            data = list(
                filter(
                    lambda s: all(
                        map(
                            lambda t: t.strip().lower() not in s["title"].lower(),
                            GLOBAL_FILTER.split(","),
                        )
                    ),
                    data,
                )
            )

        return data

    def search_by_keyword(
        self, keyword: str, count: int
    ) -> List[dict]:  # pragma: no cover
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

        :param keyword: search key word
        :type keyword: str
        :param count: how many page to fetch from website
        :type count: int

        :return: list of episode search result
        :rtype: list[dict]
        """
        raise NotImplementedError

    def fetch_bangumi_calendar(self,) -> List[WebsiteBangumi]:  # pragma: no cover
        """
        return a list of all bangumi and a list of all subtitle group

        list of bangumi dict:
        update time should be one of ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Unknown']
        """
        raise NotImplementedError

    def fetch_episode_of_bangumi(
        self, bangumi_id: str, max_page: int, subtitle_list: Optional[List[str]] = None
    ) -> List[dict]:  # pragma: no cover
        """
        get all episode by bangumi id
        example
        ```
            [
                {
                    "download": "magnet:?xt=urn:btih:e43b3b6b53dd9fd6af1199e112d3c7ff15cab82c",
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
        :param max_page: how many page to crawl
        :type max_page: int
        :return: list of bangumi
        :rtype: list[dict]
        """
        raise NotImplementedError

    def fetch_single_bangumi(
        self,
        bangumi_id: str,
        subtitle_list: Optional[List[str]] = None,
        max_page: int = int(MAX_PAGE),
    ) -> Optional[WebsiteBangumi]:
        """
        fetch bangumi info when updating, return ``None``
        if website don't have a page contains episodes and info at same time.

        SubClass doesn't have to implement this method.

        :param bangumi_id: bangumi_id, bangumi['keyword']
        :param subtitle_list: list of subtitle group
        :param max_page: how many page to crawl
        """
        return None
