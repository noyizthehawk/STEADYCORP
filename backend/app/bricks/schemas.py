"""Brick request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.fields import Field

from app.models.enums import BrickStatus


class BrickReveal(BaseModel):
    """Public view of a brick — what a visitor sees after typing its code.

    Deliberately omits internal columns (owner_id, held_until, drop_id).
    """

    model_config = ConfigDict(from_attributes=True)

    number: int
    title: str
    image_url: str
    price_cents: int
    status: BrickStatus


class BrickCreateIn(BaseModel):
    number: int = Field(ge=1, le=20)  # which brick (#1–#20)
    title: str
    image_url: str
    price_cents: int = Field(gt=0)


class ClaimOut(BaseModel):
    """Returned when a claim succeeds — what the buyer owes + their hold clock."""

    model_config = ConfigDict(from_attributes=True)

    number: int
    title: str
    image_url: str
    price_cents: int
    held_until: datetime
