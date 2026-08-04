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
    # Public navigation code shown on Instagram, e.g. "DROP01". Unique across drops.
    code = Column(String, unique=True, index=True, nullable=False)
    # Human title for the monthly collection.
    title = Column(String, nullable=False)
    # The moment the drop opens; before this, bricks can't be claimed.
    go_live_at = Column(DateTime, nullable=False)
    status = Column(Enum(DropStatus), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
