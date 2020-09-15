import time
from collections import defaultdict
from itertools import chain
from typing import Any, Dict, List, Optional, Tuple, TypeVar

from bgmi.config import MAX_PAGE
from bgmi.lib.models import (
    STATUS_FOLLOWED,
    STATUS_UPDATED,
    STATUS_UPDATING,
    Bangumi,
    Filter,
    Subtitle,
)
from bgmi.utils import parse_episode
from bgmi.website.model import Episode, WebsiteBangumi

T = TypeVar("T", bound=dict)


class BaseWebsite:
    parse_episode = staticmethod(parse_episode)

    @staticmethod
    def save_bangumi(data: WebsiteBangumi) -> None:
        """save bangumi to database"""
        b, obj_created = Bangumi.get_or_create(
            keyword=data.keyword, defaults=data.dict()
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

    def get_maximum_episode(
        self,
        bangumi: Bangumi,
        ignore_old_row: bool = True,
        max_page: int = MAX_PAGE,
    ) -> Tuple[int, List[Episode]]:
        followed_filter_obj, _ = Filter.get_or_create(bangumi_name=bangumi.name)

        info = self.fetch_single_bangumi(
            bangumi.keyword,
            subtitle_list=followed_filter_obj.subtitle_group_split,
            max_page=max_page,
        )
        if info is not None:
            self.save_bangumi(info)
            data = followed_filter_obj.apply_on_episodes(info.episodes)
        else:
            data = self.fetch_episode_of_bangumi(
                bangumi_id=bangumi.keyword,
                max_page=max_page,
                subtitle_list=followed_filter_obj.subtitle_group_split,
            )

        for episode in data:
            episode.name = bangumi.name

        if ignore_old_row:
            data = [
                row for row in data if row.time > int(time.time()) - 3600 * 24 * 30 * 3
            ]  # three month

        if data:
            b = max(data, key=lambda _i: _i.episode)
            return b.episode, data
        else:
            return 0, []

    def fetch_episode(
        self,
        _id: str,
        name: str = "",
        subtitle_list: str = None,
        max_page: int = MAX_PAGE,
    ) -> List[Episode]:
        result = []

        max_page = int(max_page)

        if subtitle_list and subtitle_list.split(", "):
            condition = subtitle_list.split(", ")
            response_data = self.fetch_episode_of_bangumi(
                bangumi_id=_id, subtitle_list=condition, max_page=max_page
            )
        else:
            response_data = self.fetch_episode_of_bangumi(
                bangumi_id=_id, max_page=max_page
            )

        for info in response_data:
            if "合集" not in info.title:
                info.name = name
                result.append(info)

        return result

    def search_by_keyword(
        self, keyword: str, count: int
    ) -> List[Episode]:  # pragma: no cover
        """

        :param keyword: search key word
        :param count: how many page to fetch from website
        :return: list of episode search result
        """
        raise NotImplementedError

    def fetch_bangumi_calendar(self) -> List[WebsiteBangumi]:  # pragma: no cover
        """
        return a list of all bangumi and a list of all subtitle group

        list of bangumi dict, update time should be one of
        ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Unknown']
        """
        raise NotImplementedError

    def fetch_episode_of_bangumi(
        self, bangumi_id: str, max_page: int, subtitle_list: Optional[List[str]] = None
    ) -> List[Episode]:  # pragma: no cover
        """
        get all episode by bangumi id

        :param bangumi_id: bangumi_id
        :param subtitle_list: list of subtitle group
        :param max_page: how many page to crawl
        :return: list of bangumi
        """
        raise NotImplementedError

    def fetch_single_bangumi(
        self,
        bangumi_id: str,
        subtitle_list: Optional[List[str]] = None,
        max_page: int = MAX_PAGE,
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
