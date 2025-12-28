# ============================================================================
# STATUS MODEL (SQLAlchemy)
# ============================================================================
from datetime import datetime
from sqlalchemy import String, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AbstractAttributEntity


class Status(AbstractAttributEntity):
    """Status entity"""
    __tablename__ = "status"
    __table_args__ = (
        Index("idx_status_codep", "code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    label: Mapped[str | None] = mapped_column(String)
    message: Mapped[str | None] = mapped_column(Text)

    def __repr__(self):
        return f"<Status(id={self.id}, code={self.code}, label={self.label})>"

