from typing import List

from pydantic import BaseModel

from .bangumi_base import UpdateTime
from .status import BangumiStatus


class BangumiItem(BaseModel):
    id: int
    name: str
    cover: str
    status: BangumiStatus = BangumiStatus.UPDATING
    update_time: UpdateTime
    subtitle_group: List[str]
    keyword: str
    data_source_id: str
    bangumi_id: int
