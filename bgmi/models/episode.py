from typing import Optional

from pydantic import BaseModel


class Episode(BaseModel):
    download: str
    subtitle_group: Optional[str]
    title: str
    episode: int
    time: int = 0
