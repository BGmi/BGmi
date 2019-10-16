from pydantic import BaseModel


class Subtitle(BaseModel):
    id: str
    name: str
    data_source_id: str
