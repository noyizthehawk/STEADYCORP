"""Auth endpoints — register / login / logout / me.

The URL prefix (/api/auth) and tags are applied where this router is included,
in app/main.py — so this file just defines handlers.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.schemas import LoginIn, RegisterIn, UserOut
from app.config import get_settings
from app.core.security import (
    COOKIE_NAME,
    DUMMY_HASH,
    hash_password,
    normalize_email,
    verify_password,
)
from app.core.sessions import create_session, revoke
from app.db import get_db
from app.models.user import User

settings = get_settings()

router = APIRouter()


def _set_session_cookie(response: Response, token: str):  # set session cookie(one place DRY AF)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,  # js cant read it. no xxx
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.session_ttl_minutes * 60,
        path="/",
    )


@router.post("/login", response_model=UserOut)
def login(login_request_data: LoginIn, response: Response, db: Session = Depends(get_db)):
    # normalize the email first
    email = normalize_email(login_request_data.email)
    # look up the user
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        verify_password(login_request_data.password, DUMMY_HASH)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(login_request_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # create the session and set the cookie
    token = create_session(user.id)
    _set_session_cookie(response, token)
    return user


@router.post("/register", response_model=UserOut, status_code=201)
def register(register_request_data: RegisterIn, response: Response, db: Session = Depends(get_db)):
    # normalize the email first
    email = normalize_email(register_request_data.email)

    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="Email already registered")
    # hash passoword
    hashed_password = hash_password(register_request_data.password)
    # create user
    user = User(email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)

    # create the session and set the cookie
    token = create_session(user.id)
    _set_session_cookie(response, token)

    return user


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response):
    # revoke the session in Redis (if there is one), then clear the cookie.
    # not gated on being logged in — logout is idempotent and always succeeds.
    token = request.cookies.get(COOKIE_NAME)
    if token:
        revoke(token)
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
