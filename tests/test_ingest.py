from datetime import UTC, datetime

from sqlalchemy import func, select

from app.models import Repository
from app.schemas.github import GitHubRepository
from app.services.ingest import upsert_repositories

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
