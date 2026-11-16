from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Comment(Base):
    __tablename__ = "comments"

    comment_gh_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    issue_gh_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("issues.issue_gh_id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    author_association: Mapped[str] = mapped_column(String)
    author_type: Mapped[str] = mapped_column(String)

    __table_args__ = (Index("ix_comments_issue_gh_id_created_at", "issue_gh_id", "created_at"),)
