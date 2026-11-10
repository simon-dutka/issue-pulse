from datetime import UTC, datetime

import httpx
import pytest

from app.core.config import Settings
from app.services.github_client import GithubClient
from app.services.github_errors import GitHubAPIError, GitHubNotFound, RateLimitExceeded

TEST_TOKEN = "test-token"


@pytest.fixture
def make_client():
    def _make(handler):
        settings = Settings(github_token=TEST_TOKEN, _env_file=None)
        transport = httpx.MockTransport(handler)

        return GithubClient(settings, transport=transport)

    return _make


def test_get_returns_response_on_success(make_client):
    def handler(request):
        return httpx.Response(200, json={})

    client = make_client(handler)

    response = client._get("/rate_limit")

    assert response.status_code == 200


def test_get_raises_not_found_on_404(make_client):
    def handler(request):
        return httpx.Response(404, json={})

    client = make_client(handler)

    with pytest.raises(GitHubNotFound):
        client._get("/rate_limit")


@pytest.mark.parametrize(
    "status_code",
    [403, 429],
)
def test_get_raises_rate_limit_when_quota_exhausted(make_client, status_code):
    def handler(request):
        return httpx.Response(
            status_code,
            json={},
            headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1700000000"},
        )

    client = make_client(handler)

    with pytest.raises(RateLimitExceeded) as exc_info:
        client._get("/rate_limit")

    assert exc_info.value.reset_at == datetime.fromtimestamp(1700000000, tz=UTC)


@pytest.mark.parametrize(
    "status_code",
    [403, 500],
)
def test_get_raises_api_error_on_non_rate_limit_failure(make_client, status_code):
    def handler(request):
        return httpx.Response(
            status_code,
            json={},
            headers={"X-RateLimit-Remaining": "4000"},
        )

    client = make_client(handler)
    with pytest.raises(GitHubAPIError):
        client._get("/rate_limit")


def test_get_stores_rate_limit_from_headers(make_client):
    def handler(request):
        return httpx.Response(
            200,
            json={},
            headers={"X-RateLimit-Remaining": "4000", "X-RateLimit-Reset": "1700000000"},
        )

    client = make_client(handler)

    client._get("/rate_limit")

    assert client._remaining == 4000
    assert client._reset_at == datetime.fromtimestamp(1700000000, tz=UTC)
