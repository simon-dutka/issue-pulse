import pytest

from app.schemas.github import GitHubIssue


@pytest.fixture
def issue_data():
    data = {
        "id": 1,
        "number": 42,
        "title": "Fix typo",
        "state": "open",
        "comments": 0,
        "created_at": "2026-01-01T10:00:00Z",
        "updated_at": "2026-01-02T10:00:00Z",
        "closed_at": None,
        "html_url": "https://github.com/o/r/issues/42",
        "author_association": "NONE",
        "state_reason": None,
        "user": {"type": "User"},
        "labels": [{"name": "good first issue"}],
        "assignee": None,
        "body": "secret text",
    }

    return data


def test_issue_model_parses_fields(issue_data):
    issue = GitHubIssue.model_validate(issue_data)

    assert issue.number == 42


def test_issue_model_drops_body(issue_data):
    issue = GitHubIssue.model_validate(issue_data)

    assert "body" not in issue.model_dump()
