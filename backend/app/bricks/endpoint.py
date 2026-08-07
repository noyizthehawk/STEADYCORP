"""Public brick endpoints — reveal a brick by its drop code + number."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import require_admin
from app.bricks.schemas import BrickCreateIn, BrickReveal
from app.db import get_db
from app.models.brick import Brick
from app.models.drop import Drop
from app.models.enums import DropStatus

router = APIRouter()


@router.get("/drops/{drop_code}/bricks/{number}", response_model=BrickReveal)
def get_brick(drop_code: str, number: int, db: Session = Depends(get_db)):
    # the drop must exist AND be live (no previewing draft/future drops)
    drop = db.scalar(select(Drop).where(Drop.code == drop_code))
    if drop is None or drop.status != DropStatus.live:
        raise HTTPException(status_code=404, detail="Nothing here.")

    # find the brick within that drop
    brick = db.scalar(select(Brick).where(Brick.drop_id == drop.id, Brick.number == number))
    if brick is None:
        raise HTTPException(status_code=404, detail="Nothing here.")

    return brick


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
