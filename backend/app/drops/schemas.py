"""Drop request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DropStatus


class DropCreateIn(BaseModel):
    code: str = Field(min_length=1, max_length=32)  # e.g. "DROP01"
    title: str = Field(min_length=1)
    go_live_at: datetime  # when the drop opens (ISO 8601)


class DropOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    go_live_at: datetime
    status: DropStatus
    created_at: datetime
