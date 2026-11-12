from datetime import UTC, datetime

import httpx
import pytest

from app.core.config import Settings
from app.services.github_client import GitHubClient
from app.services.github_errors import GitHubAPIError, GitHubNotFound, RateLimitExceeded

TEST_TOKEN = "test-token"


@pytest.fixture
def make_client():
    def _make(handler):
        settings = Settings(github_token=TEST_TOKEN, _env_file=None)
        transport = httpx.MockTransport(handler)

        return GitHubClient(settings, transport=transport)

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


def test_get_sends_auth_and_user_agent_headers(make_client):
    received = []

    def handler(request):
        received.append(request)
        return httpx.Response(
            200,
            json={},
        )

    client = make_client(handler)

    client._get("/rate_limit")

    sent = received[0]

    assert sent.headers["Authorization"] == f"Bearer {TEST_TOKEN}"
    assert "issue-pulse" in sent.headers["User-Agent"]


def test_get_blocks_request_when_remaining_below_threshold(make_client):
    calls = []

    def handler(request):
        calls.append(request)

        return httpx.Response(
            200,
            json={},
            headers={"X-RateLimit-Remaining": "5", "X-RateLimit-Reset": "1700000000"},
        )

    client = make_client(handler)

    client._get("/rate_limit")

    with pytest.raises(RateLimitExceeded):
        client._get("/rate_limit")

    assert len(calls) == 1


@pytest.fixture
def repo_data():
    data = {
        "id": 1,
        "full_name": "psf/requests",
        "html_url": "https://github.com/psf/requests",
        "language": "Python",
        "stargazers_count": 100,
        "forks_count": 10,
        "open_issues_count": 5,
        "pushed_at": "2026-01-02T10:00:00Z",
        "created_at": "2026-01-01T10:00:00Z",
        "archived": False,
        "has_issues": True,
        "description": "ignored",
    }

    return data


def test_get_repository_returns_parsed_model(make_client, repo_data):
    received = []

    def handler(request):
        received.append(request)

        return httpx.Response(200, json=repo_data)

    client = make_client(handler)

    repository = client.get_repository("psf", "requests")

    assert repository.full_name == repo_data["full_name"]
    assert received[0].url.path == "/repos/psf/requests"


def make_issue(number, is_pr=False):
    data = {
        "id": number,
        "number": number,
        "title": f"Issue {number}",
        "state": "open",
        "comments": 0,
        "created_at": "2026-01-01T10:00:00Z",
        "updated_at": "2026-01-02T10:00:00Z",
        "closed_at": None,
        "html_url": f"https://github.com/o/r/issues/{number}",
        "author_association": "NONE",
        "state_reason": None,
        "user": {"type": "User"},
        "labels": [],
        "assignee": None,
    }

    if is_pr:
        data["pull_request"] = {"url": "x"}

    return data


def test_fetch_issues_follows_pagination_and_skips_pull_requests(make_client):
    requests = []

    def handler(request):
        requests.append(request)

        page_number = request.url.params.get("page")

        if page_number == "2":
            return httpx.Response(200, json=[make_issue(3)])
        else:
            return httpx.Response(
                200,
                json=[make_issue(1), make_issue(2, is_pr=True)],
                headers={"Link": '<https://api.github.com/repos/o/r/issues?page=2>; rel="next"'},
            )

    client = make_client(handler)
    numbers = [issue.number for issue in client.fetch_issues("o", "r")]

    assert numbers == [1, 3]
    assert len(requests) == 2


def test_fetch_issues_sends_query_params(make_client):
    requests = []

    def handler(request):
        requests.append(request)

        return httpx.Response(
            200,
            json=[],
        )

    client = make_client(handler)
    since = datetime(2026, 1, 1, tzinfo=UTC)

    list(client.fetch_issues("o", "r", since=since))

    params = requests[0].url.params

    assert params["state"] == "all"
    assert params["sort"] == "updated"
    assert params["direction"] == "desc"
    assert params["per_page"] == "100"
    assert params["since"] == "2026-01-01T00:00:00+00:00"


def test_get_ignores_rate_limit_state_of_search_resource(make_client):
    requests = []

    def handler(request):
        requests.append(request)

        if request.url.path == "/core":
            return httpx.Response(
                200,
                json={},
                headers={
                    "X-RateLimit-Remaining": "4000",
                    "X-RateLimit-Reset": "1700000000",
                    "X-RateLimit-Resource": "core",
                },
            )
        else:
            return httpx.Response(
                200,
                json={},
                headers={
                    "X-RateLimit-Remaining": "5",
                    "X-RateLimit-Reset": "1700000060",
                    "X-RateLimit-Resource": "search",
                },
            )

    client = make_client(handler)

    client._get("/core")
    client._get("/search")

    assert client._remaining == 4000
    assert client._reset_at == datetime.fromtimestamp(1700000000, tz=UTC)


def test_get_raises_rate_limit_for_search_resource(make_client):
    requests = []

    def handler(request):
        requests.append(request)

        return httpx.Response(
            403,
            json={},
            headers={
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "1700000060",
                "X-RateLimit-Resource": "search",
            },
        )

    client = make_client(handler)

    with pytest.raises(RateLimitExceeded) as exc_info:
        client._get("/search")

    assert exc_info.value.reset_at == datetime.fromtimestamp(1700000060, tz=UTC)


def make_repo(number):
    data = {
        "id": number,
        "full_name": f"o/r{number}",
        "html_url": f"https://github.com/o/r{number}",
        "language": "Python",
        "stargazers_count": 100,
        "forks_count": 10,
        "open_issues_count": 5,
        "pushed_at": "2026-01-02T10:00:00Z",
        "created_at": "2026-01-01T10:00:00Z",
        "archived": False,
        "has_issues": True,
    }

    return data


@pytest.mark.parametrize(
    "max_pages, expected_names",
    [(None, ["o/r1", "o/r2"]), (1, ["o/r1"])],
)
def test_search_repositories_follows_pagination_and_respects_max_pages(
    make_client, max_pages, expected_names
):
    requests = []

    def handler(request):
        requests.append(request)

        if len(requests) > 5:
            raise AssertionError("pagination did not stop")

        page_number = request.url.params.get("page")

        if page_number == "2":
            return httpx.Response(200, json={"items": [make_repo(2)]})
        else:
            return httpx.Response(
                200,
                json={"items": [make_repo(1)]},
                headers={
                    "Link": '<https://api.github.com/search/repositories?q=x&page=2>; rel="next"'
                },
            )

    client = make_client(handler)

    repositories = list(client.search_repositories("topic:python", max_pages=max_pages))

    assert [repository.full_name for repository in repositories] == expected_names
    assert len(requests) == len(expected_names)
