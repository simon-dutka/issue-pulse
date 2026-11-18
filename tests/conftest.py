import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Base


@pytest.fixture(scope="session")
def engine():
    settings = get_settings()
    test_database_url = settings.test_database_url

    if not test_database_url:
        pytest.skip("TEST_DATABASE_URL is not set")

    if settings.database_url is not None:
        if test_database_url.get_secret_value() == settings.database_url.get_secret_value():
            raise RuntimeError("TEST_DATABASE_URL cannot be the same value as DATABASE_URL")

    engine = create_engine(test_database_url.get_secret_value())

    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
