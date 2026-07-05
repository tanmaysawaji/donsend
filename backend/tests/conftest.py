import os
from collections.abc import Generator

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401  — registers tables on Base.metadata
from app.db.base import Base

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://donsend:password@localhost:5432/donsend",
)
TEST_SCHEMA = "test"


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    admin_engine = create_engine(TEST_DATABASE_URL)
    with admin_engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {TEST_SCHEMA}"))

    engine = admin_engine.execution_options(
        schema_translate_map={None: TEST_SCHEMA}
    )
    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    with admin_engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
    admin_engine.dispose()


@pytest.fixture()
def db_session(engine: Engine) -> Generator[Session, None, None]:
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.rollback()
    session.close()
