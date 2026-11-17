from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    database_url = get_settings().database_url

    if database_url is None:
        raise RuntimeError("DATABASE_URL is empty")

    return create_engine(database_url.get_secret_value(), pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


@contextmanager
def session_scope() -> Generator[Session]:
    session = get_session_factory()()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()

        raise
    finally:
        session.close()
