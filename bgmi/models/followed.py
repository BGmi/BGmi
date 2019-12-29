from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel

from bgmi.models.status import FollowedStatus
from bgmi.pure_utils import split_str_to_list

if TYPE_CHECKING:
    from bgmi.lib import db_models


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
    def parse_db_models(cls, f: 'db_models.Followed') -> 'Followed':
        return cls(
            bangumi_id=f.bangumi_id,
            episode=f.episode,
            status=f.status,
            updated_time=f.updated_time or 0,
            data_source=split_str_to_list(f.data_source),
            subtitle=split_str_to_list(f.subtitle),
            include=split_str_to_list(f.include),
            exclude=split_str_to_list(f.exclude),
            regex=f.regex,
        )
