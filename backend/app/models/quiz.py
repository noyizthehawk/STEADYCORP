"""Quiz gate models.

The purchase gate is a timed, multiple-choice culture quiz. ``QuizQuestion`` is
the rotating pool; ``QuizSession`` is the server-authoritative record of an
in-progress attempt (which questions were issued, when, and the running streak).
The client never receives ``correct_index`` — grading happens server-side.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)

from app.db import Base
from app.models.enums import QuizSessionStatus


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id = Column(Integer, primary_key=True, index=True)
    # Nullable drop_id: NULL = global bank; set = themed to a specific drop.
    drop_id = Column(Integer, ForeignKey("drops.id"), nullable=True, index=True)
    prompt = Column(String, nullable=False)
    options = Column(JSON, nullable=False)  # list[str] of choices
    correct_index = Column(Integer, nullable=False)  # server-side only
    category = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class QuizSession(Base):
    __tablename__ = "quiz_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    brick_id = Column(Integer, ForeignKey("bricks.id"), nullable=False, index=True)
    question_ids = Column(JSON, nullable=False)  # ordered list[int] of issued questions
    current_index = Column(Integer, nullable=False, default=0)
    streak = Column(Integer, nullable=False, default=0)
    issued_at = Column(DateTime, nullable=False)  # when the current question was served
    expires_at = Column(DateTime, nullable=False)
    status = Column(Enum(QuizSessionStatus), nullable=False, default=QuizSessionStatus.open)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
