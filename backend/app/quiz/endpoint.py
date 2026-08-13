"""Quiz endpoints — author questions (admin), start a run, answer a question.

Wire into the app in main.py:
    app.include_router(router, prefix="/api", tags=["quiz"])
"""

import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_admin
from app.bricks.schemas import ClaimOut
from app.bricks.service import claim_brick, is_claimable
from app.config import get_settings
from app.db import get_db
from app.models.brick import Brick
from app.models.drop import Drop
from app.models.enums import DropStatus, QuizSessionStatus
from app.models.quiz import QuizQuestion, QuizSession
from app.models.user import User
from app.quiz.schemas import (
    AdminCreateQuizQuestion,
    AdminQuizQuestionOut,
    AnswerIn,
    AnswerOut,
    FirstQuizSession,
)

settings = get_settings()

router = APIRouter()

# ── endpoints (simplest → hardest) ──
# Step 1  POST /quiz/questions                            — require_admin, author a question
# Step 2  POST /drops/{code}/bricks/{number}/quiz/start   — get_current_user, start a run
# Step 3  POST /quiz/{session_id}/answer                  — get_current_user, grade + advance


@router.post(
    "/quiz/questions",
    status_code=201,
    response_model=AdminQuizQuestionOut,
    dependencies=[Depends(require_admin)],
)
def author_question(request: AdminCreateQuizQuestion, db: Session = Depends(get_db)):
    # make sure that the question doesn't already exist
    quiz_question_db = db.scalar(select(QuizQuestion).where(QuizQuestion.prompt == request.prompt))
    if quiz_question_db is not None:
        raise HTTPException(status_code=409, detail="Question already exists")
    question = QuizQuestion(
        prompt=request.prompt,
        options=request.options,
        correct_index=request.correct_index,
        category=request.category,
        drop_id=request.drop_id,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.post("/drops/{code}/bricks/{number}/quiz/start", response_model=FirstQuizSession)
def start_quiz(
    code: str,
    number: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # the drop must exist and be live
    drop = db.scalar(select(Drop).where(Drop.code == code))
    if drop is None or drop.status != DropStatus.live:
        raise HTTPException(404, "Drop not found")

    # the brick must exist and still be claimable (available or an expired hold),
    # matching the revealdon't waste the client's time otherwise
    brick = db.scalar(select(Brick).where(Brick.drop_id == drop.id, Brick.number == number))
    if brick is None:
        raise HTTPException(404, "Brick not found")
    if not is_claimable(brick):
        raise HTTPException(409, "Gone")

    # pick N random questions
    n = settings.quiz_questions_per_run
    pool = db.scalars(
        select(QuizQuestion.id).where(
            (QuizQuestion.drop_id.is_(None)) | (QuizQuestion.drop_id == drop.id)
        )
    ).all()
    if len(pool) < n:
        raise HTTPException(409, "Quiz not available,there muse be N questions")
    question_ids = random.sample(pool, k=n)  # sample from pool

    session = QuizSession(  # make a session
        user_id=user.id,
        brick_id=brick.id,
        question_ids=question_ids,
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # send back the first question (Client shape — no correct_index)
    first_q = db.get(QuizQuestion, session.question_ids[0])
    return FirstQuizSession(
        session_id=session.id,
        question=first_q,
        required_correct=settings.quiz_required_correct,
        total_questions=settings.quiz_questions_per_run,
        seconds_per_question=settings.quiz_seconds_per_question,
        answered=0,
        correct=0,
    )


@router.post("/quiz/{session_id}/answer", response_model=AnswerOut)
def answer(
    session_id: int,
    answer: AnswerIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_session = db.get(QuizSession, session_id)
    if user_session is None:
        raise HTTPException(404, "Session not found")
    if user_session.user_id != user.id:
        raise HTTPException(403, "You can't answer this session")
    if user_session.status != QuizSessionStatus.open:
        raise HTTPException(409, "This run is over")

    # force utc before comparing
    expires_at = user_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(410, "Session expired")

    n = settings.quiz_questions_per_run
    k = settings.quiz_required_correct

    # grade the curerent question
    question = db.get(QuizQuestion, user_session.question_ids[user_session.current_index])

    # per-question timer: a late answer just counts as wrong
    issued_at = user_session.issued_at
    if issued_at.tzinfo is None:
        issued_at = issued_at.replace(tzinfo=timezone.utc)
    elapsed = (datetime.now(timezone.utc) - issued_at).total_seconds()
    on_time = elapsed <= settings.quiz_seconds_per_question  # on time 10 seconds

    if on_time and answer.choice_index == question.correct_index:  # if correct and on time
        user_session.correct_count += 1
    user_session.current_index += 1  # mve to the next question

    answered = user_session.current_index  # else it is wrong
    correct = user_session.correct_count  # donest count correct
    wrong = answered - correct

    # decide the outcome
    if correct >= k:  # >3 exit early
        user_session.status = QuizSessionStatus.passed
        result, next_question = "passed", None
    elif answered >= n or wrong > (n - k):
        user_session.status = QuizSessionStatus.failed
        result, next_question = "failed", None
    else:
        user_session.issued_at = datetime.now(timezone.utc)  # start the next question's clock
        result = "next"
        next_question = db.get(QuizQuestion, user_session.question_ids[answered])

    db.commit()
    return AnswerOut(
        result=result,
        question=next_question,
        answered=answered,
        correct=correct,
        required_correct=k,
        total_questions=n,
    )


@router.post("/quiz/{session_id}/claim", response_model=ClaimOut)
def claim(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # did the user pass the quiz
    user_session = db.get(QuizSession, session_id)
    if user_session is None:
        raise HTTPException(404, "Session not found")
    if user_session.user_id != user.id:
        raise HTTPException(403, "You can't claim this session")
    if user_session.status != QuizSessionStatus.passed:
        raise HTTPException(403, "You must pass the quiz first")

    # now funnel to claim brick if all the conditioons pass

    outcome = claim_brick(db, user.id, user_session.brick_id)
    if outcome == "gone":
        raise HTTPException(409, "Brick already claimed by another user")

    brick = db.get(Brick, user_session.brick_id)
    db.refresh(brick)  # "It gets the updated data from the DB and loads it into memory."
    return ClaimOut(
        number=brick.number,
        title=brick.title,
        image_url=brick.image_url,
        price_cents=brick.price_cents,
        held_until=brick.held_until,
    )
