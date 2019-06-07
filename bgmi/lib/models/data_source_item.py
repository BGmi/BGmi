from typing import List, Optional

from pydantic import BaseModel

from bgmi.lib import db_models

from .bangumi_base import UpdateTime


class DataSourceItem(BaseModel):
    name: str
    cover: str
    subject_id: Optional[int]
    update_time: UpdateTime
    status: db_models.Bangumi.STATUS = 0
    subtitle_group: List[str]
    data_source_id: str
    keyword: str
