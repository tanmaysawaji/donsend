from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import hash_password
from app.db.models import InviteCode, User
from app.schemas.auth import RegisterRequest, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


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
