import pytest
from pydantic import ValidationError

from app.schemas.github import GitHubComment, GitHubIssue


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


@pytest.mark.parametrize(
    "assignee_input, expected",
    [
        (None, False),
        ({"type": "User"}, True),
    ],
)
def test_issue_model_converts_assignee_to_bool(issue_data, assignee_input, expected):
    issue_data["assignee"] = assignee_input

    issue = GitHubIssue.model_validate(issue_data)

    assert issue.assignee == expected


def test_issue_model_pull_request_defaults_to_none(issue_data):
    issue = GitHubIssue.model_validate(issue_data)

    assert issue.pull_request is None


def test_issue_model_keeps_pull_request(issue_data):
    issue_data["pull_request"] = {"url": "x"}

    issue = GitHubIssue.model_validate(issue_data)

    assert issue.pull_request == {"url": "x"}


def test_issue_model_rejects_invalid_comments(issue_data):
    issue_data["comments"] = "abc"

    with pytest.raises(ValidationError):
        GitHubIssue.model_validate(issue_data)


@pytest.fixture
def comment_data():
    data = {
        "id": 1,
        "issue_url": "https://api.github.com/repos/o/r/issues/42",
        "created_at": "2026-01-01T10:00:00Z",
        "author_association": "MEMBER",
        "user": {"type": "User", "login": "alice"},
        "body": "secret text",
    }

    return data


def test_comment_model_extracts_issue_number(comment_data):
    comment = GitHubComment.model_validate(comment_data)

    assert comment.issue_number == 42


def test_comment_model_drops_body_and_login(comment_data):
    comment = GitHubComment.model_validate(comment_data)

    assert "body" not in comment.model_dump()
    assert comment.model_dump()["user"] == {"type": "User"}
