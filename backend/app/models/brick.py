from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)

from app.db import Base
from app.models.enums import BrickStatus


class Brick(Base):
    __tablename__ = "bricks"
    id = Column(Integer, primary_key=True, index=True)
    drop_id = Column(Integer, ForeignKey("drops.id"), nullable=False, index=True)
    number = Column(Integer, nullable=False)  # 1..20 within the drop
    title = Column(String, nullable=False)  # the artwork's public name
    image_url = Column(String, nullable=False)  # R2 public URL
    price_cents = Column(Integer, nullable=False)  # money as integer cents
    status = Column(Enum(BrickStatus), nullable=False, default=BrickStatus.available)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    held_until = Column(DateTime, nullable=True)  # set on available -> held
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("drop_id", "number", name="uq_brick_drop_number"),)
