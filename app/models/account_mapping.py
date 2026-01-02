# ==================== AccountMapping Model ====================
from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import AbstractAttributEntity


class AccountMapping(AbstractAttributEntity):
    """
    Account mapping model - maps GU3 (internal) account codes to GU1 (external) account codes
    Equivalent to Java AccountMapping class

    Used for translating internal account identifiers to external partner account identifiers
    """

    __tablename__ = "account_mapping"

    __table_args__ = (
        Index("idx_account_mapping_code_gu3_deleted", "code_gu3", "deleted"),
        Index("idx_account_mapping_code_gu1_deleted", "code_gu1", "deleted"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code_gu3: Mapped[str] = mapped_column(String(100), nullable=False, comment="Internal account code")
    code_gu1: Mapped[str] = mapped_column(String(100), nullable=False, comment="External account code")
    account_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    def __repr__(self):
        return f"AccountMapping(id={self.id}, code_gu3={self.code_gu3}, code_gu1={self.code_gu1})"