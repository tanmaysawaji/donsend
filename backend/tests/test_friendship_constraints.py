import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Friendship, FriendshipStatus, User


def make_user(db_session: Session, email: str, username: str) -> User:
    user = User(email=email, username=username, password_hash="hash")
    db_session.add(user)
    db_session.flush()
    return user


def test_valid_friendship_request_succeeds(db_session: Session) -> None:
    alice = make_user(db_session, "alice@x.com", "alice")
    bob = make_user(db_session, "bob@x.com", "bob")
    user_a, user_b = sorted([alice, bob], key=lambda u: u.id)

    friendship = Friendship(
        user_a_id=user_a.id,
        user_b_id=user_b.id,
        requested_by_id=user_a.id,
        status=FriendshipStatus.PENDING,
    )
    db_session.add(friendship)
    db_session.flush()

    assert friendship.id is not None


def test_pair_must_be_stored_in_ascending_order(db_session: Session) -> None:
    alice = make_user(db_session, "alice@x.com", "alice")
    bob = make_user(db_session, "bob@x.com", "bob")
    user_a, user_b = sorted([alice, bob], key=lambda u: u.id)

    backwards = Friendship(
        user_a_id=user_b.id,
        user_b_id=user_a.id,
        requested_by_id=user_a.id,
        status=FriendshipStatus.PENDING,
    )
    db_session.add(backwards)
    with pytest.raises(IntegrityError, match="ck_friendships_pair_order"):
        db_session.flush()


def test_requested_by_must_be_a_pair_member(db_session: Session) -> None:
    alice = make_user(db_session, "alice@x.com", "alice")
    bob = make_user(db_session, "bob@x.com", "bob")
    charlie = make_user(db_session, "charlie@x.com", "charlie")
    user_a, user_b = sorted([alice, bob], key=lambda u: u.id)

    friendship = Friendship(
        user_a_id=user_a.id,
        user_b_id=user_b.id,
        requested_by_id=charlie.id,
        status=FriendshipStatus.PENDING,
    )
    db_session.add(friendship)
    with pytest.raises(
        IntegrityError, match="ck_friendships_requested_by_is_pair_member"
    ):
        db_session.flush()


def test_pair_is_unique(db_session: Session) -> None:
    alice = make_user(db_session, "alice@x.com", "alice")
    bob = make_user(db_session, "bob@x.com", "bob")
    user_a, user_b = sorted([alice, bob], key=lambda u: u.id)

    first = Friendship(
        user_a_id=user_a.id,
        user_b_id=user_b.id,
        requested_by_id=user_a.id,
        status=FriendshipStatus.PENDING,
    )
    db_session.add(first)
    db_session.flush()

    duplicate = Friendship(
        user_a_id=user_a.id,
        user_b_id=user_b.id,
        requested_by_id=user_b.id,
        status=FriendshipStatus.PENDING,
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError, match="uq_friendships_pair"):
        db_session.flush()


def test_status_rejects_values_outside_the_enum(db_session: Session) -> None:
    alice = make_user(db_session, "alice@x.com", "alice")
    bob = make_user(db_session, "bob@x.com", "bob")
    user_a, user_b = sorted([alice, bob], key=lambda u: u.id)

    # Raw SQL bypasses SQLAlchemy's Python-side Enum validation, so this
    # actually exercises the database-level CHECK constraint — the backstop
    # for any writer that isn't going through the ORM's Enum type.
    with pytest.raises(IntegrityError, match="friendshipstatus"):
        db_session.execute(
            text(
                "INSERT INTO friendships "
                "(user_a_id, user_b_id, requested_by_id, status) "
                "VALUES (:a, :b, :r, 'bogus')"
            ),
            {"a": user_a.id, "b": user_b.id, "r": user_a.id},
        )
