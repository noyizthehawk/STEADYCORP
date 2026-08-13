"""Order / checkout / collection schemas."""

from pydantic import BaseModel, ConfigDict


class CheckoutOut(BaseModel):
    checkout_url: str  # the hosted Stripe page the client redirects to


class CollectionBrick(BaseModel):
    """A brick the user owns (sold)."""

    model_config = ConfigDict(from_attributes=True)

    number: int
    title: str
    image_url: str
    price_cents: int
