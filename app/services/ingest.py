from datetime import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Repository
from app.schemas.github import GitHubRepository


def upsert_repositories(
    session: Session, repositories: list[GitHubRepository], synced_at: datetime
) -> None:
    if len(repositories) == 0:
        return

    rows = [
        {
            "repository_gh_id": repository.id,
            "full_name": repository.full_name,
            "html_url": repository.html_url,
            "language": repository.language,
            "stargazers_count": repository.stargazers_count,
            "forks_count": repository.forks_count,
            "open_issues_count": repository.open_issues_count,
            "license_spdx": repository.license_spdx,
            "has_issues": repository.has_issues,
            "archived": repository.archived,
            "pushed_at": repository.pushed_at,
            "created_at": repository.created_at,
            "repository_synced_at": synced_at,
        }
        for repository in repositories
    ]

    stmt = insert(Repository).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Repository.repository_gh_id],
        set_={name: stmt.excluded[name] for name in rows[0] if name != "repository_gh_id"},
    )
    session.execute(stmt)
