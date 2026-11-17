import pytest

from app.core.config import Settings

TEST_TOKEN = "test-token"


@pytest.fixture
def settings_data():
    data = {
        "github_token": TEST_TOKEN,
        "database_url": "postgresql+psycopg://user:secret-pass@localhost:5433/db",
        "_env_file": None,
    }

    return data


def test_settings_database_url_defaults_to_none(settings_data):
    settings_data.pop("database_url")

    settings = Settings(**settings_data)

    assert settings.database_url is None


def test_settings_database_url_is_readable_as_secret(settings_data):
    settings = Settings(**settings_data)

    assert settings_data["database_url"] == settings.database_url.get_secret_value()


def test_settings_database_url_hides_password_in_repr(settings_data):
    settings = Settings(**settings_data)

    assert "secret-pass" not in repr(settings)


def test_settings_test_database_url_defaults_to_none(settings_data):
    settings = Settings(**settings_data)

    assert settings.test_database_url is None
