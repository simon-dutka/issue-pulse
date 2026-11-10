import httpx
import pytest

from app.core.config import Settings
from app.services.github_client import GithubClient
from app.services.github_errors import GitHubNotFound

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
