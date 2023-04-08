import time
from collections import defaultdict
from typing import Any, List, Optional, TypeVar

import sqlalchemy as sa

from bgmi.config import cfg
from bgmi.lib.table import Bangumi, Followed, NotFoundError, Session, Subtitle
from bgmi.utils import parse_episode
from bgmi.website.model import Episode, WebsiteBangumi

T = TypeVar("T", bound=dict)


class BaseWebsite:
    parse_episode = staticmethod(parse_episode)

    @staticmethod
    def save_bangumi(data: WebsiteBangumi) -> None:
        """save bangumi to database"""
        with Session.begin() as session:
            subtitle_group = sorted([x.id for x in data.subtitle_group])
            try:
                b = Bangumi.get(Bangumi.id == data.id)

                b.cover = data.cover
                b.update_day = data.update_day
                b.status = Bangumi.STATUS_UPDATING
                b.subtitle_group = subtitle_group

                session.add(b)
            except NotFoundError:
                session.add(
                    Bangumi(
                        name=data.name,
                        id=data.id,
                        update_day=data.update_day,
                        cover=data.cover,
                        status=Bangumi.STATUS_UPDATING,
                        subtitle_group=subtitle_group,
                    )
                )

        for subtitle in data.subtitle_group:
            with Session.begin() as session:
                s = session.scalar(sa.select(Subtitle).where(Subtitle.id == subtitle.id))
                if s:
                    s.name = subtitle.name
                else:
                    session.add(Subtitle(id=subtitle.id, name=subtitle.name))

    def fetch(self, group_by_weekday: bool = True) -> Any:
        bangumi_result = self.fetch_bangumi_calendar()
        if not bangumi_result:
            print("can't fetch anything from website")
            return []

        Bangumi.delete_all()
        for bangumi in bangumi_result:
            self.save_bangumi(bangumi)

        if group_by_weekday:
            result_group_by_weekday = defaultdict(list)
            for bangumi in bangumi_result:
                result_group_by_weekday[bangumi.update_day.lower()].append(bangumi)
            return result_group_by_weekday
        return bangumi_result

    def get_maximum_episode(
        self,
        bangumi: Bangumi,
        ignore_old_row: bool = True,
        max_page: int = cfg.max_path,
    ) -> List[Episode]:
        followed = Followed.get(Followed.bangumi_name == bangumi.name)

        info = self.fetch_single_bangumi(
            bangumi.id,
            subtitle_list=followed.subtitle,
            max_page=max_page,
        )
        if info is not None:
            self.save_bangumi(info)
            data = followed.apply_on_episodes(info.episodes)
        else:
            data = self.fetch_episode_of_bangumi(
                bangumi_id=bangumi.id,
                max_page=max_page,
                subtitle_list=followed.subtitle,
            )
            data = followed.apply_on_episodes(data)

        for episode in data:
            episode.name = bangumi.name

        if ignore_old_row:
            data = [row for row in data if row.time > int(time.time()) - 3600 * 24 * 30 * 3]  # three month

        return data

    def fetch_episode(
        self,
        _id: str,
        name: str = "",
        subtitle_list: Optional[str] = None,
        max_page: int = cfg.max_path,
    ) -> List[Episode]:
        result = []

        max_page = int(max_page)

        if subtitle_list and subtitle_list.split(", "):
            condition = subtitle_list.split(", ")
            response_data = self.fetch_episode_of_bangumi(bangumi_id=_id, subtitle_list=condition, max_page=max_page)
        else:
            response_data = self.fetch_episode_of_bangumi(bangumi_id=_id, max_page=max_page)

        for info in response_data:
            if "合集" not in info.title:
                info.name = name
                result.append(info)

        return result

    def search_by_keyword(self, keyword: str, count: int) -> List[Episode]:  # pragma: no cover
        """

        :param keyword: search key word
        :param count: how many page to fetch from website
        :return: list of episode search result
        """
        raise NotImplementedError

    def search_by_tag(self, tag: str, subtitle: Optional[str] = None, count: Optional[int] = None) -> List[Episode]:
        """

        :param tag: search tag
        :param subtitle: search subtitle group name
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
        max_page: int = cfg.max_path,
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
