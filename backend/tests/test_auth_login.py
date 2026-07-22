from fastapi.testclient import TestClient
from sqlalchemy import select
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


def test_login_succeeds_with_correct_credentials(
    client: TestClient, db_session: Session
) -> None:
    make_user(db_session, password="correct horse")

    response = client.post(
        "/auth/login", json={"email": "alice@x.com", "password": "correct horse"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]

    set_cookie = response.headers["set-cookie"]
    assert "refresh_token=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=strict" in set_cookie
    assert "Secure" in set_cookie
    assert "Path=/auth" in set_cookie


def test_login_rejects_wrong_password(client: TestClient, db_session: Session) -> None:
    make_user(db_session, password="correct horse")

    response = client.post(
        "/auth/login", json={"email": "alice@x.com", "password": "wrong horse"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_rejects_unknown_email(client: TestClient) -> None:
    response = client.post(
        "/auth/login", json={"email": "nobody@x.com", "password": "whatever"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_second_login_rotates_the_existing_session(
    client: TestClient, db_session: Session
) -> None:
    make_user(db_session, password="correct horse")

    first = client.post(
        "/auth/login", json={"email": "alice@x.com", "password": "correct horse"}
    )
    first_refresh_token = first.cookies["refresh_token"]

    second = client.post(
        "/auth/login", json={"email": "alice@x.com", "password": "correct horse"}
    )
    second_refresh_token = second.cookies["refresh_token"]

    assert first_refresh_token != second_refresh_token

    sessions = db_session.execute(select(UserSession)).scalars().all()
    assert len(sessions) == 1
    assert sessions[0].refresh_token_hash == hash_refresh_token(second_refresh_token)
