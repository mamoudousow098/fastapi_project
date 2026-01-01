"""
Updated Flow model with cancellation support
"""
from sqlalchemy import Boolean, Index, String, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.models import AbstractAttributEntity
from app.models.enums import CommissionBaseEnum


class Flow(AbstractAttributEntity):
    __tablename__ = "flow"

    __table_args__ = (
        Index("idx_flow_code", "code"),
        Index("idx_flow_service_code", "service_code"),
        Index("idx_flow_code_deleted", "code", "deleted"),
        Index("idx_flow_is_cancellation", "is_cancellation"),  # New index
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    label: Mapped[str | None] = mapped_column(String)
    code: Mapped[str | None] = mapped_column(String)

    application_date: Mapped[datetime | None] = mapped_column(DateTime)

    product_code: Mapped[str | None] = mapped_column(String)
    service_code: Mapped[str | None] = mapped_column(String)

    account_number: Mapped[str | None] = mapped_column(String)
    client_category: Mapped[str | None] = mapped_column(String)

    commission_base: Mapped[CommissionBaseEnum] = mapped_column(
        Enum(CommissionBaseEnum),
        default=CommissionBaseEnum.NOMINAL_AMOUNT
    )

    version: Mapped[str | None] = mapped_column(String)

    # New column for cancellation flows
    is_cancellation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=True,
        comment="Indicates if this flow is for cancellation operations"
    )

    # Relations
    rules = relationship(
        "ImpactRule",
        cascade="all, delete-orphan",
        back_populates="flow"
    )

    constraints: Mapped[list["Constraint"]] = relationship(
        "Constraint",
        back_populates="flow",
        cascade="all, delete-orphan"
    )

    provider = relationship(
        "ServiceProvider",
        back_populates="flow",
        uselist=False,
        cascade="all, delete"
    )