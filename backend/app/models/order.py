from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String

from app.db import Base
from app.models.enums import OrderStatus


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    brick_id = Column(Integer, ForeignKey("bricks.id"), nullable=False, index=True)
    stripe_external_id = Column(String, unique=True, nullable=False, index=True)
    amount_cents = Column(Integer, nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.pending)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
