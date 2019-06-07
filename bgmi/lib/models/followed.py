from typing import List, Optional

from pydantic import BaseModel

from bgmi import config
from bgmi.lib import db_models
from bgmi.lib.db_models._tables import split_str_to_list
from bgmi.lib.models import Episode
from bgmi.lib.models.status import FollowedStatus
from bgmi.utils.followed_filter import apply_regex


class Followed(BaseModel):
    bangumi_id: int
    episode: int = 0
    status: FollowedStatus
    updated_time: int = 0
    data_source: List[str] = []
    subtitle: List[str] = []
    include: List[str] = []
    exclude: List[str] = []
    regex: Optional[str]

    @classmethod
    def parse_db_models(cls, f: db_models.Followed) -> 'Followed':
        return cls(
            bangumi_id=f.bangumi_id,
            episode=f.episode,
            status=f.status,
            update_time=f.updated_time,
            data_source=split_str_to_list(f.data_source),
            subtitle=split_str_to_list(f.subtitle),
            include=split_str_to_list(f.include),
            exclude=split_str_to_list(f.exclude),
            regex=f.regex,
        )

    def apply_keywords_filter_on_list_of_episode(
        self,
        episode_list: List[Episode],
    ) -> List[Episode]:
        episode_list = self.apply_include(episode_list)
        episode_list = self.apply_exclude(episode_list)
        episode_list = self._apply_regex(episode_list)
        return episode_list

    def apply_include(self, episode_list: List[Episode]) -> List[Episode]:
        if self.include:

            def f1(s: Episode):
                return all(map(lambda t: t in s.title, self.include))

            episode_list = list(filter(f1, episode_list))
        return episode_list

    def apply_exclude(self, episode_list: List[Episode]) -> List[Episode]:
        if self.exclude:
            exclude = self.exclude
        else:
            exclude = []
        if config.ENABLE_GLOBAL_FILTER != '0':
            exclude += split_str_to_list(config.GLOBAL_FILTER)
        exclude.append('合集')

        def f2(s: Episode):
            return not any(map(lambda t: t in s.title, exclude))

        episode_list = list(filter(f2, episode_list))
        return episode_list

    def _apply_regex(self, episode_list: List[Episode]) -> List[Episode]:
        if self.regex:
            return apply_regex(self.regex, episode_list)
        return episode_list
