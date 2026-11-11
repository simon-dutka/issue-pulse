from collections.abc import Iterator
from datetime import UTC, datetime

import httpx

from app.core.config import Settings, get_settings
from app.schemas.github import GitHubIssue, GitHubRepository
from app.services.github_errors import GitHubAPIError, GitHubNotFound, RateLimitExceeded


class GitHubClient:
    def __init__(
        self, settings: Settings | None = None, transport: httpx.BaseTransport | None = None
    ):
        if settings is None:
            settings = get_settings()

        headers = {
            "Authorization": f"Bearer {settings.github_token.get_secret_value()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": settings.github_user_agent,
        }

        self._client = httpx.Client(
            base_url=settings.github_api_url, headers=headers, timeout=30, transport=transport
        )
        self._min_remaining = settings.github_min_remaining_requests
        self._remaining = None
        self._reset_at = None

    def close(self):
        self._client.close()

    def _get(self, path: str, params: dict | None = None) -> httpx.Response:
        if self._remaining is not None and self._remaining < self._min_remaining:
            raise RateLimitExceeded(self._reset_at)

        response = self._client.get(path, params=params)
        remaining = response.headers.get("X-RateLimit-Remaining")

        if remaining is not None:
            self._remaining = int(remaining)

        reset = response.headers.get("X-RateLimit-Reset")

        if reset is not None:
            self._reset_at = datetime.fromtimestamp(int(reset), tz=UTC)

        if response.status_code == 404:
            raise GitHubNotFound(f"{path}: {response.status_code}")
        if response.status_code in (403, 429) and self._remaining == 0:
            raise RateLimitExceeded(self._reset_at)
        if response.status_code >= 400:
            raise GitHubAPIError(f"{path}: {response.status_code}")

        return response

    def get_repository(self, owner: str, repo: str) -> GitHubRepository:
        response = self._get(f"/repos/{owner}/{repo}")
        return GitHubRepository.model_validate(response.json())

    def fetch_issues(
        self, owner: str, repo: str, since: datetime | None = None
    ) -> Iterator[GitHubIssue]:
        path = f"/repos/{owner}/{repo}/issues"

        params = {"state": "all", "sort": "updated", "direction": "desc", "per_page": 100}

        if since is not None:
            params["since"] = since.isoformat()

        while path is not None:
            response = self._get(path, params)

            for item in response.json():
                issue = GitHubIssue.model_validate(item)

                if issue.pull_request is None:
                    yield issue

            next_link = response.links.get("next")

            if next_link is not None:
                path = next_link["url"]
            else:
                path = None

            params = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
