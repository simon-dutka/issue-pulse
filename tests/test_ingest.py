from datetime import UTC, datetime

from sqlalchemy import func, select

from app.models import Issue, Repository
from app.schemas.github import GitHubIssue, GitHubRepository
from app.services.ingest import upsert_issues, upsert_repositories

FIRST_SYNC = datetime(2026, 1, 1, tzinfo=UTC)
SECOND_SYNC = datetime(2026, 1, 2, tzinfo=UTC)


def make_repository(gh_id: int, stars: int) -> GitHubRepository:
    data = {
        "id": gh_id,
        "full_name": f"o/r{gh_id}",
        "html_url": f"https://github.com/o/r{gh_id}",
        "language": "Python",
        "stargazers_count": stars,
        "forks_count": 10,
        "open_issues_count": 5,
        "pushed_at": "2026-01-02T10:00:00Z",
        "created_at": "2026-01-01T10:00:00Z",
        "archived": False,
        "has_issues": True,
    }

    return GitHubRepository.model_validate(data)


def test_upsert_repositories_inserts_new_rows(db_session):
    repositories = [make_repository(1, 10), make_repository(2, 20)]

    upsert_repositories(db_session, repositories, FIRST_SYNC)
    first_repository = db_session.get(Repository, 1)
    second_repository = db_session.get(Repository, 2)

    assert first_repository.stargazers_count == 10
    assert first_repository.full_name == "o/r1"
    assert first_repository.repository_synced_at == FIRST_SYNC
    assert first_repository.issues_synced_at is None
    assert second_repository.stargazers_count == 20


def test_upsert_repositories_updates_existing_row(db_session):
    repositories = [make_repository(1, 10)]

    upsert_repositories(db_session, repositories, FIRST_SYNC)

    repositories = [make_repository(1, 20)]

    upsert_repositories(db_session, repositories, SECOND_SYNC)

    repository = db_session.get(Repository, 1)

    count = db_session.scalar(select(func.count()).select_from(Repository))

    assert repository.stargazers_count == 20
    assert repository.repository_synced_at == SECOND_SYNC
    assert count == 1


def test_upsert_repositories_keeps_issues_synced_at(db_session):
    repositories = [make_repository(1, 10)]

    upsert_repositories(db_session, repositories, FIRST_SYNC)

    repository = db_session.get(Repository, 1)

    repository.issues_synced_at = FIRST_SYNC

    db_session.flush()

    repositories = [make_repository(1, 20)]

    upsert_repositories(db_session, repositories, SECOND_SYNC)

    db_session.refresh(repository)

    assert repository.stargazers_count == 20
    assert repository.issues_synced_at == FIRST_SYNC


def test_upsert_repositories_ignores_empty_list(db_session):
    repositories = []

    upsert_repositories(db_session, repositories, FIRST_SYNC)

    count = db_session.scalar(select(func.count()).select_from(Repository))

    assert count == 0


def make_issue(
    gh_id: int,
    number: int,
    title: str = "Issue",
    labels: list[str] | None = None,
    with_user: bool = True,
) -> GitHubIssue:
    data = {
        "id": gh_id,
        "number": number,
        "title": title,
        "state": "open",
        "comments": 0,
        "created_at": "2026-01-01T10:00:00Z",
        "updated_at": "2026-01-02T10:00:00Z",
        "closed_at": None,
        "html_url": f"https://github.com/o/r1/issues/{number}",
        "author_association": "NONE",
        "state_reason": None,
        "user": {"type": "User"},
        "assignee": None,
    }

    data["labels"] = []

    if labels is not None:
        for name in labels:
            data["labels"].append({"name": name})

    if with_user is False:
        data.pop("user")

    return GitHubIssue.model_validate(data)


def test_upsert_issues_inserts_new_rows(db_session):
    upsert_repositories(db_session, [make_repository(1, 10)], FIRST_SYNC)

    upsert_issues(db_session, 1, [make_issue(100, 1), make_issue(101, 2)])

    first_issue = db_session.get(Issue, 100)
    second_issue = db_session.get(Issue, 101)

    assert first_issue.issue_number == 1
    assert first_issue.repository_gh_id == 1
    assert first_issue.author_type == "User"
    assert first_issue.has_assignee is False
    assert second_issue.issue_number == 2


def test_upsert_issues_updates_existing_row(db_session):
    upsert_repositories(db_session, [make_repository(1, 10)], FIRST_SYNC)

    upsert_issues(db_session, 1, [make_issue(100, 1, title="Old")])
    upsert_issues(db_session, 1, [make_issue(100, 1, title="New")])

    first_issue = db_session.get(Issue, 100)

    assert first_issue.title == "New"
    assert db_session.scalar(select(func.count()).select_from(Issue)) == 1


def test_upsert_issues_keeps_last_duplicate(db_session):
    upsert_repositories(db_session, [make_repository(1, 10)], FIRST_SYNC)

    upsert_issues(
        db_session, 1, [make_issue(100, 1, title="First"), make_issue(100, 1, title="Second")]
    )

    first_issue = db_session.get(Issue, 100)

    assert first_issue.title == "Second"
    assert db_session.scalar(select(func.count()).select_from(Issue)) == 1


def test_upsert_issues_skips_issues_without_user(db_session):
    upsert_repositories(db_session, [make_repository(1, 10)], FIRST_SYNC)

    skipped_count = upsert_issues(
        db_session, 1, [make_issue(100, 1), make_issue(101, 2, with_user=False)]
    )

    assert skipped_count == 1
    assert db_session.get(Issue, 100) is not None
    assert db_session.get(Issue, 101) is None


def test_upsert_issues_stores_label_names(db_session):
    upsert_repositories(db_session, [make_repository(1, 10)], FIRST_SYNC)

    upsert_issues(db_session, 1, [make_issue(100, 1, labels=["bug", "good first issue"])])

    assert db_session.get(Issue, 100).labels == ["bug", "good first issue"]


def test_upsert_issues_keeps_first_maintainer_response_at(db_session):
    upsert_repositories(db_session, [make_repository(1, 10)], FIRST_SYNC)

    upsert_issues(db_session, 1, [make_issue(100, 1, title="Old")])

    issue = db_session.get(Issue, 100)

    issue.first_maintainer_response_at = FIRST_SYNC

    db_session.flush()

    upsert_issues(db_session, 1, [make_issue(100, 1, title="New")])

    db_session.refresh(issue)

    assert issue.title == "New"
    assert issue.first_maintainer_response_at == FIRST_SYNC
