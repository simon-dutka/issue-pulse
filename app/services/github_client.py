import httpx

from app.core.config import Settings, get_settings


class GithubClient:
    def __init__(self, settings: Settings | None = None):
        if settings is None:
            settings = get_settings()

        headers = {
            "Authorization": f"Bearer {settings.github_token.get_secret_value()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": settings.github_user_agent,
        }

        self._client = httpx.Client(base_url=settings.github_api_url, headers=headers, timeout=30)

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
