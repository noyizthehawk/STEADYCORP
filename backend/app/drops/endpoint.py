"""Drop endpoints — admin creates drops (public drop reads can be added later)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import require_admin
from app.db import get_db
from app.drops.schemas import DropCreateIn, DropOut
from app.models.drop import Drop
from app.models.enums import DropStatus

router = APIRouter()


@router.post(
    "/drops",
    status_code=201,
    response_model=DropOut,
    dependencies=[Depends(require_admin)],
)
def create_drop(payload: DropCreateIn, db: Session = Depends(get_db)):
    # Normalize the code so it matches how visitors type it (frontend uppercases).
    code = payload.code.strip().upper()

    # code must be unique across drops
    existing = db.scalar(select(Drop).where(Drop.code == code))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Drop code already exists")

    # New drops start as draft — admin adds bricks, then flips it live.
    drop = Drop(
        code=code,
        title=payload.title,
        go_live_at=payload.go_live_at,
        status=DropStatus.draft,
    )
    db.add(drop)
    db.commit()
    db.refresh(drop)
    return drop


@router.post(
    "/drops/{code}/publish",
    response_model=DropOut,
    dependencies=[Depends(require_admin)],
)
def publish_drop(code: str, db: Session = Depends(get_db)):
    drop = db.scalar(select(Drop).where(Drop.code == code.strip().upper()))
    if drop is None:
        raise HTTPException(status_code=404, detail="Drop does not exist")
    # Only a draft can be published — don't revive a closed drop or re-publish a live one.
    if drop.status != DropStatus.draft:
        raise HTTPException(status_code=409, detail="Only a draft drop can be published")

    # Mutate the loaded row and commit — that's how you update an existing record.
    drop.status = DropStatus.live
    db.commit()
    db.refresh(drop)
    return drop
