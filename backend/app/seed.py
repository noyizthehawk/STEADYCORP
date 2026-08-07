"""Seed the dev database with an admin, a test user, and a live drop + bricks.

Run:  make seed        (or:  python -m app.seed)

Idempotent — safe to run repeatedly; it skips anything that already exists.
Assumes migrations have been applied (`make upgrade`).
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models  # noqa: F401  (register all models on Base.metadata)
from app.core.security import hash_password
from app.db import SessionLocal
from app.models.brick import Brick
from app.models.drop import Drop
from app.models.enums import BrickStatus, DropStatus
from app.models.user import User

ADMIN_EMAIL, ADMIN_PASSWORD = "admin@steadycorp.test", "adminpass123"
USER_EMAIL, USER_PASSWORD = "user@steadycorp.test", "userpass123"
DROP_CODE = "DROP01"

BRICKS = [
    {"number": 1, "title": "Cobalt Moth", "price_cents": 5000},
    {"number": 2, "title": "Rustveil", "price_cents": 6500},
    {"number": 3, "title": "Nine of Swords", "price_cents": 8000},
]


def _get_or_create_user(db: Session, email: str, password: str, is_admin: bool) -> bool:
    if db.scalar(select(User).where(User.email == email)):
        return False
    db.add(User(email=email, hashed_password=hash_password(password), is_admin=is_admin))
    db.commit()
    return True


def seed() -> None:
    db = SessionLocal()
    try:
        admin_new = _get_or_create_user(db, ADMIN_EMAIL, ADMIN_PASSWORD, is_admin=True)
        user_new = _get_or_create_user(db, USER_EMAIL, USER_PASSWORD, is_admin=False)

        drop = db.scalar(select(Drop).where(Drop.code == DROP_CODE))
        if drop is None:
            drop = Drop(
                code=DROP_CODE,
                title="Inaugural Drop",
                go_live_at=datetime.now(timezone.utc),
                status=DropStatus.live,  # seed goes straight to live for easy testing
            )
            db.add(drop)
            db.commit()
            db.refresh(drop)

        new_bricks = 0
        for b in BRICKS:
            exists = db.scalar(
                select(Brick).where(Brick.drop_id == drop.id, Brick.number == b["number"])
            )
            if exists is None:
                db.add(
                    Brick(
                        drop_id=drop.id,
                        status=BrickStatus.available,
                        image_url=f"https://placehold.co/600x600/000/fff?text=BRICK+{b['number']:02d}",
                        **b,
                    )
                )
                new_bricks += 1
        db.commit()

        a = "(new)" if admin_new else "(existing)"
        u = "(new)" if user_new else "(existing)"
        nums = [b["number"] for b in BRICKS]
        print("── seed complete ─────────────────────────────")
        print(f"  admin : {ADMIN_EMAIL} / {ADMIN_PASSWORD}  {a}")
        print(f"  user  : {USER_EMAIL} / {USER_PASSWORD}  {u}")
        print(f"  drop  : {DROP_CODE} [{drop.status}]  bricks {nums}  (+{new_bricks} new)")
        print("  try   : GET /api/drops/DROP01/bricks/1")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
