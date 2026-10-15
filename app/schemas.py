from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    author: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=2000)


class MessageOut(BaseModel):
    id: int
    author: str
    text: str
    created_at: datetime
