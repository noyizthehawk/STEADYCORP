"""User model.

Agreed columns:
    id                 PK
    email              unique, stored lowercased/normalized (case-insensitive login)
    hashed_password    argon2
    stripe_customer_id nullable (set on first checkout)
    created_at         server default now

You'll likely want:
    from datetime import datetime
    from sqlalchemy import String, DateTime, func
    from sqlalchemy.orm import Mapped, mapped_column
    from app.db import Base

# class User(Base):
#     __tablename__ = "users"
#     # columns here
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, false

from app.db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    # The login identifier. unique=True means the DB itself forbids two users same adress
    email = Column(String, unique=True, index=True, nullable=False)
    # We store the bcrypt HASH of the password, never the password itself
    hashed_password = Column(String, nullable=False)
    # When the account was created.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    stripe_customer_id = Column(String, nullable=True)
    # Only admins can create drops / bricks / quiz questions.
    is_admin = Column(Boolean, nullable=False, default=False, server_default=false())
