from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Comment, Issue, Repository
from app.schemas.github import GitHubComment, GitHubIssue, GitHubRepository


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


def upsert_comments(session: Session, repository_gh_id: int, comments: list[GitHubComment]) -> int:
    issues_stmt = select(Issue.issue_number, Issue.issue_gh_id).where(
        Issue.repository_gh_id == repository_gh_id
    )

    result = session.execute(issues_stmt)

    issue_gh_id_by_number = {number: gh_id for number, gh_id in result}

    kept_comments = []
    skipped_count = 0

    for comment in comments:
        if comment.author_type is None:
            skipped_count += 1
        elif comment.issue_number not in issue_gh_id_by_number:
            skipped_count += 1
        else:
            kept_comments.append(comment)

    comments_by_id = {comment.id: comment for comment in kept_comments}
    unique_comments = list(comments_by_id.values())

    if len(unique_comments) == 0:
        return skipped_count

    rows = [
        {
            "comment_gh_id": comment.id,
            "issue_gh_id": issue_gh_id_by_number[comment.issue_number],
            "created_at": comment.created_at,
            "author_association": comment.author_association,
            "author_type": comment.author_type,
        }
        for comment in unique_comments
    ]

    stmt = insert(Comment).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Comment.comment_gh_id],
        set_={name: stmt.excluded[name] for name in rows[0] if name != "comment_gh_id"},
    )

    session.execute(stmt)

    return skipped_count
