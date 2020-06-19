from operator import attrgetter
from typing import TYPE_CHECKING

import attr

from bgmi.lib.constants import BANGUMI_UPDATE_TIME

if TYPE_CHECKING:
    from typing import List


@attr.s
class Episode:
    title = attr.ib(type=str)
    download = attr.ib(type=str)
    episode = attr.ib(default=0, type=int)
    time = attr.ib(default=0, type=int)
    subtitle_group = attr.ib(default="", type=str)
    name = attr.ib(default="", type=str)


@attr.s
class SubtitleGroup:
    id = attr.ib(type=str)
    name = attr.ib(type=str)


@attr.s
class WebsiteBangumi:
    keyword = attr.ib(type=str)
    update_time = attr.ib(
        default="Unknown", type=str, validator=attr.validators.in_(BANGUMI_UPDATE_TIME)
    )
    name = attr.ib(default="", type=str)
    status = attr.ib(default=0, type=int)
    subtitle_group = attr.ib(factory=list)  # type: List[SubtitleGroup]
    cover = attr.ib(default="", type=str)
    episodes = attr.ib(factory=list)  # type: List[Episode]

    @property
    def max_episode(self) -> int:
        return max(self.episodes, key=attrgetter("episode")).episode
