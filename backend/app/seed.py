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
from app.models.quiz import QuizQuestion
from app.models.user import User

ADMIN_EMAIL, ADMIN_PASSWORD = "admin@steadycorp.test", "adminpass123"
USER_EMAIL, USER_PASSWORD = "user@steadycorp.test", "userpass123"
DROP_CODE = "DROP01"

BRICKS = [
    {"number": 1, "title": "Cobalt Moth", "price_cents": 5000},
    {"number": 2, "title": "Rustveil", "price_cents": 6500},
    {"number": 3, "title": "Nine of Swords", "price_cents": 8000},
]

# Global culture-trivia pool (drop_id=None). Needs at least quiz_questions_per_run.
QUIZ_QUESTIONS = [
    {
        "prompt": "Which city is the birthplace of grime?",
        "options": ["Manchester", "London", "Birmingham", "Bristol"],
        "correct_index": 1,
    },
    {
        "prompt": "In music, what does BPM stand for?",
        "options": ["Bars Per Minute", "Bass Per Measure", "Beats Per Measure", "Beats Per Minute"],
        "correct_index": 3,
    },
    {
        "prompt": "Grime typically runs at around what tempo?",
        "options": ["140 BPM", "120 BPM", "100 BPM", "160 BPM"],
        "correct_index": 0,
    },
    {
        "prompt": "Who released the 2016 album 'Konnichiwa'?",
        "options": ["Stormzy", "Wiley", "Skepta", "Kano"],
        "correct_index": 2,
    },
    {
        "prompt": "Who is known as the 'Godfather of Grime'?",
        "options": ["Dizzee Rascal", "Wiley", "Skepta", "JME"],
        "correct_index": 1,
    },
    {
        "prompt": "Dizzee Rascal's 'Boy in da Corner' won which 2003 award?",
        "options": ["Brit Award", "Grammy", "Ivor Novello", "Mercury Prize"],
        "correct_index": 3,
    },
    {
        "prompt": "Street artist Banksy is originally associated with which city?",
        "options": ["Bristol", "London", "Manchester", "Liverpool"],
        "correct_index": 0,
    },
    {
        "prompt": "Which crew did Skepta co-found?",
        "options": ["Roll Deep", "So Solid Crew", "Boy Better Know", "Ruff Sqwad"],
        "correct_index": 2,
    },
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

        new_questions = 0
        for q in QUIZ_QUESTIONS:
            exists = db.scalar(select(QuizQuestion).where(QuizQuestion.prompt == q["prompt"]))
            if exists is None:
                db.add(QuizQuestion(drop_id=None, **q))
                new_questions += 1
        db.commit()

        a = "(new)" if admin_new else "(existing)"
        u = "(new)" if user_new else "(existing)"
        nums = [b["number"] for b in BRICKS]
        print("── seed complete ─────────────────────────────")
        print(f"  admin : {ADMIN_EMAIL} / {ADMIN_PASSWORD}  {a}")
        print(f"  user  : {USER_EMAIL} / {USER_PASSWORD}  {u}")
        print(f"  drop  : {DROP_CODE} [{drop.status}]  bricks {nums}  (+{new_bricks} new)")
        print(f"  quiz  : {len(QUIZ_QUESTIONS)} questions in pool  (+{new_questions} new)")
        print("  try   : GET /api/drops/DROP01/bricks/1")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
