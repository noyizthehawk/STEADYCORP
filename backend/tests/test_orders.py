"""fulfill_order — the idempotent webhook fulfillment (mark paid + sold, exactly once)."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import StaticPool, create_engine, select
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.db import Base
from app.models.brick import Brick
from app.models.drop import Drop
from app.models.enums import BrickStatus, DropStatus, OrderStatus
from app.models.order import Order
from app.models.user import User
from app.orders.service import fulfill_order

NAIVE = datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine, expire_on_commit=False)()
    yield s
    s.close()


def _setup(db, *, held_by_owner=True):
    user = User(email="u@t", hashed_password="x")
    drop = Drop(code="D", title="d", go_live_at=NAIVE, status=DropStatus.live)
    db.add_all([user, drop])
    db.commit()
    brick = Brick(
        drop_id=drop.id,
        number=1,
        title="c",
        image_url="x",
        price_cents=5000,
        status=BrickStatus.held,
        owner_id=user.id if held_by_owner else None,
        held_until=NAIVE + timedelta(minutes=10),
    )
    db.add(brick)
    db.commit()
    order = Order(
        user_id=user.id,
        brick_id=brick.id,
        stripe_external_id="cs_test_1",
        amount_cents=5000,
        status=OrderStatus.pending,
    )
    db.add(order)
    db.commit()
    return user, brick, order


def test_fulfill_marks_paid_and_sold(db):
    _, brick, order = _setup(db)
    fulfill_order(db, "cs_test_1")
    db.refresh(order)
    db.refresh(brick)
    assert order.status == OrderStatus.paid
    assert brick.status == BrickStatus.sold


def test_fulfill_is_idempotent(db):
    _setup(db)
    fulfill_order(db, "cs_test_1")
    fulfill_order(db, "cs_test_1")  # Stripe retry → no error, no double effect
    assert db.scalar(select(Order)).status == OrderStatus.paid
    assert db.scalar(select(Brick)).status == BrickStatus.sold


def test_fulfill_unknown_session_is_noop(db):
    _setup(db)
    fulfill_order(db, "cs_never_seen")  # must not raise
    assert db.scalar(select(Order)).status == OrderStatus.pending


def test_fulfill_when_brick_no_longer_held_pays_but_does_not_sell(db):
    # hold lapsed & the brick was reclaimed by someone else (owner cleared)
    _, brick, order = _setup(db, held_by_owner=False)
    fulfill_order(db, "cs_test_1")
    db.refresh(order)
    db.refresh(brick)
    assert order.status == OrderStatus.paid  # payment happened
    assert brick.status != BrickStatus.sold  # but we couldn't hand them this brick
