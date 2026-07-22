from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, hash_refresh_token
from app.db.models import User, UserSession


def make_user(db_session: Session, *, password: str = "correct horse") -> User:
    user = User(
        email="alice@x.com", username="alice", password_hash=hash_password(password)
    )
    db_session.add(user)
    db_session.flush()
    return user


def test_refresh_succeeds_and_issues_a_new_access_token(
    client: TestClient, db_session: Session
) -> None:
    make_user(db_session, password="correct horse")
    client.post(
        "/auth/login", json={"email": "alice@x.com", "password": "correct horse"}
    )

    response = client.post("/auth/refresh")

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert "refresh_token=" in response.headers["set-cookie"]


def test_refresh_rotates_the_old_token_out(
    client: TestClient, db_session: Session
) -> None:
    make_user(db_session, password="correct horse")
    login_response = client.post(
        "/auth/login", json={"email": "alice@x.com", "password": "correct horse"}
    )
    old_refresh_token = login_response.cookies["refresh_token"]

    client.post("/auth/refresh")

    client.cookies.set("refresh_token", old_refresh_token)
    reuse_response = client.post("/auth/refresh")
    assert reuse_response.status_code == 401


def test_refresh_rejects_missing_cookie(client: TestClient) -> None:
    response = client.post("/auth/refresh")
    assert response.status_code == 401


def test_refresh_rejects_unknown_token(client: TestClient) -> None:
    client.cookies.set("refresh_token", "not-a-real-token")
    response = client.post("/auth/refresh")
    assert response.status_code == 401


def test_refresh_rejects_expired_session(
    client: TestClient, db_session: Session
) -> None:
    user = make_user(db_session, password="correct horse")
    db_session.add(
        UserSession(
            user_id=user.id,
            refresh_token_hash=hash_refresh_token("expired-token"),
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
    )
    db_session.flush()

    client.cookies.set("refresh_token", "expired-token")
    response = client.post("/auth/refresh")
    assert response.status_code == 401
