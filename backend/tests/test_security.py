from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    _JWT_ALGORITHM,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_correct_password_verifies() -> None:
    password_hash = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", password_hash) is True


def test_wrong_password_fails() -> None:
    password_hash = hash_password("correct horse battery staple")
    assert verify_password("wrong password", password_hash) is False


def test_same_password_hashes_differently_each_time() -> None:
    first = hash_password("correct horse battery staple")
    second = hash_password("correct horse battery staple")
    assert first != second


def test_access_token_round_trips_to_the_same_user_id() -> None:
    token = create_access_token(42)
    assert decode_access_token(token) == 42


def test_tampered_token_is_rejected() -> None:
    token = create_access_token(42)
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(tampered)


def test_expired_token_is_rejected() -> None:
    now = datetime.now(UTC)
    payload = {"sub": "42", "iat": now, "exp": now - timedelta(minutes=1)}
    expired_token = jwt.encode(payload, settings.secret_key, algorithm=_JWT_ALGORITHM)
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)
