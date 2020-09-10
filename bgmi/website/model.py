from operator import attrgetter
from typing import List, Optional

from pydantic import BaseModel, validator

from bgmi.lib.constants import BANGUMI_UPDATE_TIME


class Episode(BaseModel):
    title: str
    download: str
    episode: int = 0
    time: int = 0
    subtitle_group: Optional[str]
    name: str = ""

    @staticmethod
    def remove_duplicated_bangumi(result: List["Episode"]) -> List["Episode"]:
        ret = []
        episodes = list({i.episode for i in result})
        for i in result:
            if i.episode in episodes:
                ret.append(i)
                del episodes[episodes.index(i.episode)]

        return ret


class SubtitleGroup(BaseModel):
    id: str
    name: str


class WebsiteBangumi(BaseModel):
    keyword: str
    update_time: str = "Unknown"
    name: str = ""
    status: int = 0
    subtitle_group: List[SubtitleGroup] = []
    cover: str = ""
    episodes: List[Episode] = []

    @property
    def max_episode(self) -> int:
        return max(self.episodes, key=attrgetter("episode")).episode

    @validator("update_time")
    def validate_update_time(cls, v: str) -> str:
        assert v in BANGUMI_UPDATE_TIME, "update time can be only one of {}".format(
            BANGUMI_UPDATE_TIME
        )
        return v
