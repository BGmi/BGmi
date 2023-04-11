from operator import attrgetter
from typing import List, Optional

from pydantic import BaseModel, validator

from bgmi.lib.constants import BANGUMI_UPDATE_TIME


class Episode(BaseModel):
    title: str
    download: str
    episode: int = 0
    time: int = 0
    subtitle_group: Optional[str] = None
    name: str = ""

    class Config:
        orm_mode = True

    @staticmethod
    def remove_duplicated_bangumi(result: List["Episode"]) -> List["Episode"]:
        ret = []
        episodes = list({i.episode for i in result})
        for i in result:
            if i.episode in episodes:
                ret.append(i)
                del episodes[episodes.index(i.episode)]

        return ret

    def contains_any_words(self, keywords: List[str]) -> bool:
        """Keywords should be converted to low case after passed to this function."""
        title = self.title.lower()
        return any(t in title for t in keywords)


class SubtitleGroup(BaseModel):
    id: str
    name: str


class WebsiteBangumi(BaseModel):
    id: str
    update_day: str = "Unknown"
    name: str = ""
    status: int = 0
    subtitle_group: List[SubtitleGroup] = []
    cover: str = ""
    episodes: List[Episode] = []

    @property
    def max_episode(self) -> int:
        return max(self.episodes, key=attrgetter("episode")).episode

    @validator("update_day")
    def validate_update_time(cls, v: str) -> str:  # noqa: N805
        assert v in BANGUMI_UPDATE_TIME, f"update time can be only one of {BANGUMI_UPDATE_TIME}"
        return v
