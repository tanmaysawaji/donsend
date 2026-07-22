import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.models import InviteCode, User, UserSession
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])

_DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-constant-time-login")


def _set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="strict",
        path="/auth",
        max_age=int(timedelta(days=settings.refresh_token_expire_days).total_seconds()),
    )


@router.post(
    "/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> User:
    invite = db.execute(
        select(InviteCode)
        .where(InviteCode.code == request.invite_code)
        .with_for_update()
    ).scalar_one_or_none()
    if invite is None or invite.used_by_id is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Invalid or already-used invite code"
        )

    if db.execute(
        select(User).where(User.email == request.email)
    ).scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    if db.execute(
        select(User).where(User.username == request.username)
    ).scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")

    user = User(
        email=request.email,
        username=request.username,
        password_hash=hash_password(request.password),
    )
    db.add(user)
    db.flush()

    invite.used_by_id = user.id
    invite.used_at = datetime.now(UTC)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Email or username already in use"
        ) from exc

    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest, response: Response, db: Session = Depends(get_db)
) -> TokenResponse:
    user = db.execute(
        select(User).where(User.email == request.email)
    ).scalar_one_or_none()
    password_hash = user.password_hash if user is not None else _DUMMY_PASSWORD_HASH
    password_ok = verify_password(request.password, password_hash)
    if user is None or not password_ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    refresh_token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    expires_at = now + timedelta(days=settings.refresh_token_expire_days)

    user_session = db.get(UserSession, user.id)
    if user_session is None:
        user_session = UserSession(user_id=user.id)
        db.add(user_session)
    user_session.refresh_token_hash = hash_refresh_token(refresh_token)
    user_session.expires_at = expires_at
    user_session.created_at = now

    db.commit()

    _set_refresh_token_cookie(response, refresh_token)

    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
) -> TokenResponse:
    if refresh_token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing refresh token")

    user_session = db.execute(
        select(UserSession).where(
            UserSession.refresh_token_hash == hash_refresh_token(refresh_token)
        )
    ).scalar_one_or_none()

    now = datetime.now(UTC)
    if user_session is None or user_session.expires_at < now:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token"
        )

    new_refresh_token = secrets.token_urlsafe(32)
    user_session.refresh_token_hash = hash_refresh_token(new_refresh_token)
    user_session.expires_at = now + timedelta(days=settings.refresh_token_expire_days)
    user_session.created_at = now
    db.commit()

    _set_refresh_token_cookie(response, new_refresh_token)

    return TokenResponse(access_token=create_access_token(user_session.user_id))
