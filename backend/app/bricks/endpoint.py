"""Public brick endpoints — reveal a brick by its drop code + number."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import require_admin
from app.bricks.schemas import BrickCreateIn, BrickReveal
from app.bricks.service import is_claimable
from app.db import get_db
from app.models.brick import Brick
from app.models.drop import Drop
from app.models.enums import BrickStatus, DropStatus

router = APIRouter()


@router.get("/drops/{drop_code}/bricks/{number}", response_model=BrickReveal)
def get_brick(drop_code: str, number: int, db: Session = Depends(get_db)):
    # the drop must exist AND be live
    drop = db.scalar(select(Drop).where(Drop.code == drop_code))
    if drop is None or drop.status != DropStatus.live:
        raise HTTPException(status_code=404, detail="Nothing here.")

    # find the brick within that drop
    brick = db.scalar(select(Brick).where(Brick.drop_id == drop.id, Brick.number == number))
    if brick is None:
        raise HTTPException(status_code=404, detail="Nothing here.")

    # an expired hold reads as available again (same rule as claim_brick)
    status = BrickStatus.available if is_claimable(brick) else brick.status
    return BrickReveal(
        number=brick.number,
        title=brick.title,
        image_url=brick.image_url,
        price_cents=brick.price_cents,
        status=status,
    )


@router.get(
    "/drops/{code}/bricks",
    response_model=list[BrickReveal],
    dependencies=[Depends(require_admin)],
)
def list_drop_bricks(code: str, db: Session = Depends(get_db)):
    # admine only to get all bricks related to a drop
    drop = db.scalar(select(Drop).where(Drop.code == code.strip().upper()))
    if drop is None:
        raise HTTPException(status_code=404, detail="Drop does not exist")

    bricks = db.scalars(
        select(Brick).where(Brick.drop_id == drop.id).order_by(Brick.number)
    ).all()
    return [
        BrickReveal(
            number=b.number,
            title=b.title,
            image_url=b.image_url,
            price_cents=b.price_cents,
            status=BrickStatus.available if is_claimable(b) else b.status,
        )
        for b in bricks
    ]


@router.post(
    "/drops/{code}/bricks",
    status_code=201,
    response_model=BrickReveal,
    dependencies=[Depends(require_admin)],
)
def create_brick(code: str, brick_create_data: BrickCreateIn, db: Session = Depends(get_db)):
    # check if the drop exists
    drop = db.scalar(select(Drop).where(Drop.code == code))
    if drop is None:
        raise HTTPException(status_code=404, detail="Drop does not exist")
    # if drop exist create the brick but first check if brick is already created
    if (
        db.scalar(
            select(Brick).where(Brick.drop_id == drop.id, Brick.number == brick_create_data.number)
        )
        is not None
    ):
        raise HTTPException(status_code=409, detail="Brick already exists")
    brick = Brick(
        drop_id=drop.id,
        number=brick_create_data.number,
        title=brick_create_data.title,
        image_url=brick_create_data.image_url,
        price_cents=brick_create_data.price_cents,
    )
    db.add(brick)
    db.commit()
    db.refresh(brick)
    return brick
