from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import InviteCode, User


def make_invite(db_session: Session, *, used: bool = False) -> InviteCode:
    invite = InviteCode(code="test-invite-code")
    db_session.add(invite)
    db_session.flush()
    if used:
        other_user = User(
            email="someone-else@x.com",
            username="someone_else",
            password_hash="hash",
        )
        db_session.add(other_user)
        db_session.flush()
        invite.used_by_id = other_user.id
        invite.used_at = datetime.now(UTC)
        db_session.flush()
    return invite


def test_register_succeeds_with_valid_invite_code(
    client: TestClient, db_session: Session
) -> None:
    invite = make_invite(db_session)

    response = client.post(
        "/auth/register",
        json={
            "email": "alice@x.com",
            "username": "alice",
            "password": "correct horse",
            "invite_code": invite.code,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@x.com"
    assert body["username"] == "alice"
    assert "password_hash" not in body

    db_session.refresh(invite)
    assert invite.used_by_id == body["id"]
    assert invite.used_at is not None


def test_register_rejects_unknown_invite_code(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "alice@x.com",
            "username": "alice",
            "password": "correct horse",
            "invite_code": "does-not-exist",
        },
    )
    assert response.status_code == 400


def test_register_rejects_already_used_invite_code(
    client: TestClient, db_session: Session
) -> None:
    invite = make_invite(db_session, used=True)

    response = client.post(
        "/auth/register",
        json={
            "email": "alice@x.com",
            "username": "alice",
            "password": "correct horse",
            "invite_code": invite.code,
        },
    )
    assert response.status_code == 400


def test_register_rejects_duplicate_email(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(
        User(email="alice@x.com", username="alice_original", password_hash="hash")
    )
    db_session.flush()
    invite = make_invite(db_session)

    response = client.post(
        "/auth/register",
        json={
            "email": "alice@x.com",
            "username": "alice_new",
            "password": "correct horse",
            "invite_code": invite.code,
        },
    )
    assert response.status_code == 409


def test_register_rejects_duplicate_username(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(
        User(email="original@x.com", username="alice", password_hash="hash")
    )
    db_session.flush()
    invite = make_invite(db_session)

    response = client.post(
        "/auth/register",
        json={
            "email": "new@x.com",
            "username": "alice",
            "password": "correct horse",
            "invite_code": invite.code,
        },
    )
    assert response.status_code == 409


def test_register_rejects_short_password(
    client: TestClient, db_session: Session
) -> None:
    invite = make_invite(db_session)

    response = client.post(
        "/auth/register",
        json={
            "email": "alice@x.com",
            "username": "alice",
            "password": "short",
            "invite_code": invite.code,
        },
    )
    assert response.status_code == 422


def test_register_rejects_invalid_username_characters(
    client: TestClient, db_session: Session
) -> None:
    invite = make_invite(db_session)

    response = client.post(
        "/auth/register",
        json={
            "email": "alice@x.com",
            "username": "alice smith!",
            "password": "correct horse",
            "invite_code": invite.code,
        },
    )
    assert response.status_code == 422
