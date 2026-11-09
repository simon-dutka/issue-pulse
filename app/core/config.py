from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # SecretStr masks the value in logs; read it with .get_secret_value().
    github_token: SecretStr
    github_user_agent: str = "issue-pulse/0.1 (+https://github.com/simon-dutka/issue-pulse)"
    # Overridable so tests can point the client at a fake server.
    github_api_url: str = "https://api.github.com"

    # ignore unknown variables in .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Lazy & cached
@lru_cache
def get_settings() -> Settings:
    return Settings()
