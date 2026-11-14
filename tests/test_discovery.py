from datetime import date

import pytest

from app.services.discovery import build_discovery_query


@pytest.mark.parametrize(
    "min_stars, expected",
    [
        (None, "help-wanted-issues:>=3 archived:false pushed:>2026-01-01"),
        (500, "help-wanted-issues:>=3 archived:false pushed:>2026-01-01 stars:>=500"),
        (0, "help-wanted-issues:>=3 archived:false pushed:>2026-01-01 stars:>=0"),
    ],
)
def test_build_discovery_query_composes_qualifiers(min_stars, expected):
    query = build_discovery_query(3, date(2026, 1, 1), min_stars)

    assert query == expected
