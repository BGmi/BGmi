from typing import Dict, Optional

from pydantic import BaseModel

from .bangumi_base import UpdateTime
from .bangumi_item import BangumiItem
from .status import BangumiStatus


class Bangumi(BaseModel):
    id: Optional[int]
    name: str
    cover: str
    status: BangumiStatus
    subject_id: int
    update_time: UpdateTime
    has_data_source: int = 0
    data_source: Optional[Dict[str, BangumiItem]]
