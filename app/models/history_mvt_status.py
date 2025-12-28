from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class HistoryMvtStatus(Base):
    """
    History of movement status changes
    Equivalent to HistoryMvtStatus entity
    """
    __tablename__ = "status_history"
    __table_args__ = (
        Index("idx_status_history_gu_id", "gu_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    status: Mapped[str | None] = mapped_column(String)
    
    creation_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        server_default=func.now()
    )
    
    message: Mapped[str | None] = mapped_column(String)
    
    author: Mapped[str | None] = mapped_column(String)
    
    gu_id: Mapped[str | None] = mapped_column(String)