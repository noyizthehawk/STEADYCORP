"""Shared test fixtures.

Gives every test an isolated, in-memory SQLite database and a FastAPI client
whose ``get_db`` dependency is pointed at that same session. Tables are built
from ``Base.metadata`` — so the moment you write a model (and uncomment its
import in ``app/models/__init__.py``) it exists in the test DB automatically.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401  (registers models on Base.metadata)
from app.db import Base, get_db
from app.main import app


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one shared in-memory connection
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
