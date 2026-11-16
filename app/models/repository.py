from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Repository(Base):
    __tablename__ = "repositories"

    repository_gh_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    full_name: Mapped[str] = mapped_column(String)
    html_url: Mapped[str] = mapped_column(String)
    language: Mapped[str | None] = mapped_column(String)
    stargazers_count: Mapped[int] = mapped_column(Integer)
    forks_count: Mapped[int] = mapped_column(Integer)
    open_issues_count: Mapped[int] = mapped_column(Integer)
    license_spdx: Mapped[str | None] = mapped_column(String)
    has_issues: Mapped[bool] = mapped_column(Boolean)
    archived: Mapped[bool] = mapped_column(Boolean)
    pushed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    repository_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    issues_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "stargazers_count >= 0", name="ck_repositories_stargazers_count_non_negative"
        ),
        CheckConstraint("forks_count >= 0", name="ck_repositories_forks_count_non_negative"),
        CheckConstraint(
            "open_issues_count >= 0", name="ck_repositories_open_issues_count_non_negative"
        ),
    )
