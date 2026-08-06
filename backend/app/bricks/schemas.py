"""Brick request/response schemas."""

from pydantic import BaseModel, ConfigDict

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
