"""Checkout, the Stripe webhook, and 'my collection'."""

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.config import get_settings
from app.db import get_db
from app.models.brick import Brick
from app.models.enums import BrickStatus
from app.models.quiz import QuizSession
from app.models.user import User
from app.orders.schemas import CheckoutOut, CollectionBrick
from app.orders.service import create_checkout, fulfill_order

settings = get_settings()

router = APIRouter()


@router.post("/quiz/{session_id}/checkout", response_model=CheckoutOut)
def checkout(
    session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    session = db.get(QuizSession, session_id)
    if session is None:
        raise HTTPException(404, "Session not found")
    if session.user_id != user.id:
        raise HTTPException(403, "Not your session")

    # only the current holder can pay for the brick
    brick = db.get(Brick, session.brick_id)
    if brick is None or brick.status != BrickStatus.held or brick.owner_id != user.id:
        raise HTTPException(409, "You don't hold this brick")

    return CheckoutOut(checkout_url=create_checkout(db, brick, user.id))


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, settings.stripe.webhook_secret.get_secret_value()
        )
    except Exception as exc:  # bad signature / malformed payload
        raise HTTPException(status_code=400, detail="Invalid webhook") from exc

    if event["type"] == "checkout.session.completed":
        fulfill_order(db, event["data"]["object"]["id"])
    return {"received": True}


@router.get("/me/bricks", response_model=list[CollectionBrick])
def my_collection(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(
        select(Brick).where(Brick.owner_id == user.id, Brick.status == BrickStatus.sold)
    ).all()
