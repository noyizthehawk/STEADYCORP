"""Brick inventory operations — business logic (no HTTP). Home of the atomic claim."""

from datetime import datetime, timedelta, timezone
from typing import Literal

#
from sqlalchemy import and_, or_, update
from sqlalchemy.orm import Session

#
from app.config import get_settings
from app.models.brick import Brick
from app.models.enums import BrickStatus

#
settings = get_settings()
# firstcheck if brick is available with status


def claim_brick(db: Session, user_id: int, brick_id: int) -> Literal["held", "gone"]:
    # firstcheck if brick is available with status no select
    # to avoid race
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    time_to_hold = timedelta(minutes=settings.brick_hold_minutes)
    """claimable if the status is available or status is held and held_until is in the past"""
    claimable = or_(
        Brick.status == BrickStatus.available,
        and_(Brick.status == BrickStatus.held, Brick.held_until < now),
    )

    result = db.execute(  # no select we need to update in time to avoid race
        update(Brick)
        .where(Brick.id == brick_id, claimable)
        .values(status=BrickStatus.held, owner_id=user_id, held_until=now + time_to_hold)
    )
    db.commit()
    if result.rowcount == 1:
        return "held"
    # indepotency
    brick = db.get(Brick, brick_id)
    if brick and brick.status == BrickStatus.held and brick.owner_id == user_id:
        return "held"
    return "gone"
