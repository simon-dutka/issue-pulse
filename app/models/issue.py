from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Issue(Base):
    __tablename__ = "issues"

    issue_gh_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    repository_gh_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("repositories.repository_gh_id", ondelete="CASCADE")
    )
    issue_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(Text)
    html_url: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    comments_count: Mapped[int] = mapped_column(Integer)
    author_association: Mapped[str] = mapped_column(String)
    author_type: Mapped[str] = mapped_column(String)
    has_assignee: Mapped[bool] = mapped_column(Boolean)
    labels: Mapped[list[str]] = mapped_column(ARRAY(String))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_maintainer_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint(
            "repository_gh_id", "issue_number", name="uq_issues_repository_gh_id_issue_number"
        ),
        CheckConstraint("state IN ('open', 'closed')", name="ck_issues_state_valid"),
        CheckConstraint("comments_count >= 0", name="ck_issues_comments_count_non_negative"),
    )
