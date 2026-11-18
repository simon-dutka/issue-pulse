from datetime import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Issue, Repository
from app.schemas.github import GitHubIssue, GitHubRepository


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


def upsert_issues(session: Session, repository_gh_id: int, issues: list[GitHubIssue]) -> int:
    kept_issues = []
    skipped_count = 0

    for issue in issues:
        if issue.author_type is None:
            skipped_count += 1
        else:
            kept_issues.append(issue)

    issues_by_id = {}

    for issue in kept_issues:
        issues_by_id[issue.id] = issue

    unique_issues = list(issues_by_id.values())

    if len(unique_issues) == 0:
        return skipped_count

    rows = [
        {
            "issue_gh_id": issue.id,
            "repository_gh_id": repository_gh_id,
            "issue_number": issue.number,
            "title": issue.title,
            "html_url": issue.html_url,
            "state": issue.state,
            "comments_count": issue.comments,
            "author_association": issue.author_association,
            "author_type": issue.author_type,
            "has_assignee": issue.assignee,
            "labels": [label.name for label in issue.labels],
            "created_at": issue.created_at,
            "updated_at": issue.updated_at,
            "closed_at": issue.closed_at,
        }
        for issue in unique_issues
    ]

    stmt = insert(Issue).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Issue.issue_gh_id],
        set_={name: stmt.excluded[name] for name in rows[0] if name != "issue_gh_id"},
    )
    session.execute(stmt)

    return skipped_count
