"""Public brick endpoints — reveal a brick by its drop code + number."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.bricks.schemas import BrickReveal
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
