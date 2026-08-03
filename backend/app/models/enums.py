

import enum


class DropStatus(enum.StrEnum):
    draft = "draft"
    live = "live"
    closed = "closed"


class BrickStatus(enum.StrEnum):
    available = "available"
    held = "held"
    sold = "sold"


class OrderStatus(enum.StrEnum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
