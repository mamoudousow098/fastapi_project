# ==================== ServiceMapping Model ====================
from sqlalchemy import Index, String
from sqlalchemy.orm import mapped_column, Mapped

from app.models import AbstractAttributEntity


class ServiceMapping(AbstractAttributEntity):
    """
    Service mapping model - maps GU3 (internal) codes to GU1 (external) codes
    Equivalent to Java ServiceMapping class

    Used for translating internal service codes to external partner service codes
    """

    __tablename__ = "services_mapping"

    __table_args__ = (
        Index("idx_service_mapping_code_gu3_deleted", "code_gu3", "deleted"),
        Index("idx_service_mapping_code_gu1_deleted", "code_gu1", "deleted"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code_gu3: Mapped[str] = mapped_column(String(100), nullable=False, comment="Internal service code")
    code_gu1: Mapped[str] = mapped_column(String(100), nullable=False, comment="External service code")
    context: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Additional context for mapping")

    def __repr__(self):
        return f"ServiceMapping(id={self.id}, code_gu3={self.code_gu3}, code_gu1={self.code_gu1}, context={self.context})"

