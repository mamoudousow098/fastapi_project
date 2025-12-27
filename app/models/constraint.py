from sqlalchemy import String, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AbstractAttributEntity
#from app.models.service_type import ServiceType


class Constraint(AbstractAttributEntity):
    __tablename__ = "flow_constraint"

    __table_args__ = (
        Index("idx_constraint_code", "code"),
        Index("idx_constraint_code_deleted", "code", "deleted"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str] = mapped_column(String)
    value: Mapped[str | None] = mapped_column(String)

    flow_id: Mapped[int | None] = mapped_column(
        ForeignKey("flow.id")
    )

    flow = relationship(
        "Flow",
        back_populates="constraints"
    )

    service_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("service_type.id")
    )

    service_type: Mapped["ServiceType"] = relationship()
