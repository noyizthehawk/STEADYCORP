
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Integer,
    String,
)

from app.db import Base
from app.models.enums import DropStatus


class Drop(Base):
    __tablename__ = "drops"
    id = Column(Integer, primary_key=True, index=True)
    secret_name = Column(String, nullable=False)
    price_cents = Column(Integer, nullable=False)
    image_url = Column(String, nullable=False)
    go_live_at = Column(DateTime, nullable=False)
    status = Column(Enum(DropStatus), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))