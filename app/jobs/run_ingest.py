import logging
from datetime import UTC, datetime, timedelta

from app.core.database import session_scope
from app.models import Repository
from app.services.discovery import build_discovery_query
from app.services.github_client import GitHubClient
from app.services.github_errors import GitHubError, RateLimitExceeded
from app.services.ingest import ingest_repository, upsert_repositories

MIN_HELP_WANTED = 3
PUSHED_WITHIN = timedelta(days=30)
STAR_BUCKETS = [(200, 999), (1000, 4999), (5000, None)]
REPOSITORIES_PER_BUCKET = 7

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    now = datetime.now(UTC)

    pushed_after = (now - PUSHED_WITHIN).date()

    with GitHubClient() as client:
        found = []

        for min_stars, max_stars in STAR_BUCKETS:
            query = build_discovery_query(MIN_HELP_WANTED, pushed_after, min_stars, max_stars)

            found.extend(
                list(client.search_repositories(query, max_pages=1))[:REPOSITORIES_PER_BUCKET]
            )

        with session_scope() as session:
            upsert_repositories(session, found, now)

        for github_repository in found:
            if not github_repository.has_issues:
                continue

            try:
                with session_scope() as session:
                    repository = session.get(Repository, github_repository.id)

                    ingest_repository(session, client, repository, now)
            except RateLimitExceeded as error:
                logger.warning("Rate limit reached, stopping until %s", error.reset_at)
                break
            except GitHubError as error:
                logger.warning("Skipping %s: %s", github_repository.full_name, error)


if __name__ == "__main__":
    main()
