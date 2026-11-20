from datetime import date


def build_discovery_query(
    min_help_wanted: int,
    pushed_after: date,
    min_stars: int | None = None,
    max_stars: int | None = None,
) -> str:
    qualifiers = [
        f"help-wanted-issues:>={min_help_wanted}",
        "archived:false",
        f"pushed:>{pushed_after}",
    ]

    if min_stars is not None and max_stars is not None:
        qualifiers.append(f"stars:{min_stars}..{max_stars}")
    elif min_stars is not None:
        qualifiers.append(f"stars:>={min_stars}")
    elif max_stars is not None:
        qualifiers.append(f"stars:<={max_stars}")

    return " ".join(qualifiers)
