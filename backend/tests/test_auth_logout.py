from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import User, UserSession


def make_user(db_session: Session, *, password: str = "correct horse") -> User:
    user = User(
        email="alice@x.com", username="alice", password_hash=hash_password(password)
    )
    db_session.add(user)
    db_session.flush()
    return user


def test_logout_deletes_the_session_and_clears_the_cookie(
    client: TestClient, db_session: Session
) -> None:
    make_user(db_session, password="correct horse")
    client.post(
        "/auth/login", json={"email": "alice@x.com", "password": "correct horse"}
    )

    response = client.post("/auth/logout")

    assert response.status_code == 204
    set_cookie = response.headers["set-cookie"]
    assert "refresh_token=" in set_cookie
    assert "Max-Age=0" in set_cookie

    sessions = db_session.execute(select(UserSession)).scalars().all()
    assert sessions == []

    refresh_after_logout = client.post("/auth/refresh")
    assert refresh_after_logout.status_code == 401


def test_logout_without_a_cookie_still_succeeds(client: TestClient) -> None:
    response = client.post("/auth/logout")
    assert response.status_code == 204


def test_logout_with_unknown_token_still_succeeds(client: TestClient) -> None:
    client.cookies.set("refresh_token", "not-a-real-token")
    response = client.post("/auth/logout")
    assert response.status_code == 204
