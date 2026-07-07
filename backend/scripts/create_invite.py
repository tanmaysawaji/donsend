import secrets

from app.db.models import InviteCode
from app.db.session import SessionLocal


def main() -> None:
    code = secrets.token_urlsafe(16)
    with SessionLocal() as session:
        session.add(InviteCode(code=code))
        session.commit()
    print(code)


if __name__ == "__main__":
    main()
