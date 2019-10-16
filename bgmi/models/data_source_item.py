from typing import List, Optional

from pydantic import BaseModel

from bgmi.models.status import BangumiStatus

from .bangumi_base import UpdateTime


class DataSourceItem(BaseModel):
    name: str
    cover: str
    subject_id: Optional[int]
    update_time: UpdateTime
    status: BangumiStatus = BangumiStatus.UPDATING
    subtitle_group: List[str]
    data_source_id: str
    keyword: str
