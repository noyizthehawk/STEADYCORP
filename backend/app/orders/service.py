"""Order fulfillment — Stripe checkout creation + the idempotent webhook handler.

`fulfill_order` is the money-critical, exactly-once step: it marks an order paid
and its brick sold, and is safe to call repeatedly (Stripe retries webhooks).
"""

import stripe
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.brick import Brick
from app.models.enums import BrickStatus, OrderStatus
from app.models.order import Order

settings = get_settings()


def create_checkout(db: Session, brick: Brick, user_id: int) -> str:
    """Create a Stripe Checkout Session + a pending Order; return the checkout URL."""
    stripe.api_key = settings.stripe.secret_key.get_secret_value()
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"STEADY BRICK #{brick.number:02d} — {brick.title}"},
                    "unit_amount": brick.price_cents,
                },
                "quantity": 1,
            }
        ],
        success_url=f"{settings.frontend_origin}/collection?paid=1",
        cancel_url=f"{settings.frontend_origin}/store",
        # Let Stripe collect and validate a shipping address on its hosted page.
        shipping_address_collection={
            "allowed_countries": settings.shipping_allowed_countries_list
        },
        metadata={"brick_id": str(brick.id), "user_id": str(user_id)},
    )
    #add the pending order to the db
    db.add(
        Order(
            user_id=user_id,
            brick_id=brick.id,
            stripe_external_id=session.id,  # the idempotency key
            amount_cents=brick.price_cents,
            status=OrderStatus.pending,
        )
    )
    db.commit()
    return session.url


def _extract_shipping(session) -> dict | None:
    """Extract shipping details from a Stripe Checkout Session.

    Stripe's webhook gives a StripeObject (not a plain dict) whose .get() is
    shadowed by attribute lookup, so normalize to a real dict first. Tests pass
    plain dicts, which pass through unchanged.
    """
    if hasattr(session, "to_dict"):
        session = session.to_dict()
    details = (session.get("collected_information") or {}).get("shipping_details") or session.get(
        "shipping_details"
    )
    if not details:
        return None
    address = details.get("address") or {}
    return {
        "ship_name": details.get("name"),
        "ship_line1": address.get("line1"),
        "ship_line2": address.get("line2"),
        "ship_city": address.get("city"),
        "ship_region": address.get("state"),
        "ship_postal": address.get("postal_code"),
        "ship_country": address.get("country"),
    }


def fulfill_order(db: Session, stripe_session_id: str, shipping: dict | None = None) -> None:
    """Idempotently mark an order paid + its brick sold. Safe to call repeatedly."""
    order = db.scalar(select(Order).where(Order.stripe_external_id == stripe_session_id))
    if order is None or order.status == OrderStatus.paid:
        return  # unknown session, or already fulfilled

    # Sell the brick only if this user STILL holds it — guards the rare
    # expired-hold-then-reclaimed-by-someone-else edge (that case = refund territory).
    db.execute(
        update(Brick)
        .where(
            Brick.id == order.brick_id,
            Brick.owner_id == order.user_id,
            Brick.status == BrickStatus.held,
        )
        .values(status=BrickStatus.sold)
    )
    # Snapshot the shipping address onto the order (only on this first-fulfill path,
    # so webhook retries — which return early above — never overwrite it).
    if shipping:
        for column, value in shipping.items():
            setattr(order, column, value)
    order.status = OrderStatus.paid
    db.commit()
