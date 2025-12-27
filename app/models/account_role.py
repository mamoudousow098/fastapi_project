from sqlalchemy import String, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AbstractAttributEntity


class AccountRole(AbstractAttributEntity):
    __tablename__ = "account_role"
    __table_args__ = (
        Index("idx_account_role_identifier", "identifier"),
        Index("idx_account_role_identifier_deleted", "identifier", "deleted"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    identifier: Mapped[str | None] = mapped_column(String)