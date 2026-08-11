"""Correctness of the atomic claim — including the headline: many simultaneous
claims on one brick yield exactly one winner."""

import threading
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

import app.models  # noqa: F401  (register tables on Base.metadata)
from app.bricks.service import claim_brick
from app.db import Base
from app.models.brick import Brick
from app.models.drop import Drop
from app.models.enums import BrickStatus, DropStatus
from app.models.user import User

NAIVE = datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture
def make_session(tmp_path):
    """Sessionmaker on a file-based SQLite (WAL) so threads get real, separate connections."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'claim.db'}",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,  # each session → its own connection (real concurrency)
    )

    @event.listens_for(engine, "connect")
    def _pragmas(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=30000")
        cur.close()

    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _seed(
    session_factory, *, n_users=1, status=BrickStatus.available, held_until=None, owner_ix=None
):
    db = session_factory()
    drop = Drop(code="D", title="d", go_live_at=NAIVE, status=DropStatus.live)
    db.add(drop)
    db.commit()
    db.refresh(drop)
    users = [User(email=f"u{i}@t", hashed_password="x") for i in range(n_users)]
    db.add_all(users)
    db.commit()
    uids = [u.id for u in users]
    brick = Brick(
        drop_id=drop.id,
        number=1,
        title="c",
        image_url="x",
        price_cents=100,
        status=status,
        held_until=held_until,
        owner_id=uids[owner_ix] if owner_ix is not None else None,
    )
    db.add(brick)
    db.commit()
    bid = brick.id
    db.close()
    return uids, bid


def test_claim_available(make_session):
    (uid,), bid = _seed(make_session)
    db = make_session()
    assert claim_brick(db, uid, bid) == "held"
    assert db.get(Brick, bid).owner_id == uid


def test_idempotent_double_click(make_session):
    (uid,), bid = _seed(make_session)
    db = make_session()
    assert claim_brick(db, uid, bid) == "held"
    assert claim_brick(db, uid, bid) == "held"


def test_gone_for_other_valid_hold(make_session):
    uids, bid = _seed(
        make_session,
        n_users=2,
        status=BrickStatus.held,
        held_until=NAIVE + timedelta(minutes=10),
        owner_ix=0,
    )
    db = make_session()
    assert claim_brick(db, uids[1], bid) == "gone"


def test_expired_hold_reclaimed(make_session):
    uids, bid = _seed(
        make_session,
        n_users=2,
        status=BrickStatus.held,
        held_until=NAIVE - timedelta(minutes=1),
        owner_ix=0,
    )
    db = make_session()
    assert claim_brick(db, uids[1], bid) == "held"
    assert db.get(Brick, bid).owner_id == uids[1]


def test_sold_never_reclaimed(make_session):
    uids, bid = _seed(
        make_session,
        n_users=2,
        status=BrickStatus.sold,
        held_until=NAIVE - timedelta(minutes=1),
        owner_ix=0,
    )
    db = make_session()
    assert claim_brick(db, uids[1], bid) == "gone"


def test_concurrent_claims_exactly_one_winner(make_session):
    n = 20
    uids, bid = _seed(make_session, n_users=n)
    results: dict[int, str] = {}
    barrier = threading.Barrier(n)

    def worker(uid: int):
        barrier.wait()  # release all threads together → maximum contention
        db = make_session()
        try:
            results[uid] = claim_brick(db, uid, bid)
        finally:
            db.close()

    threads = [threading.Thread(target=worker, args=(uid,)) for uid in uids]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    winners = [uid for uid, r in results.items() if r == "held"]
    assert len(winners) == 1, f"expected exactly ONE winner, got {len(winners)}: {winners}"

    db = make_session()
    brick = db.get(Brick, bid)
    assert brick.status == BrickStatus.held
    assert brick.owner_id == winners[0]
