from sqlalchemy import String, Integer, ForeignKey, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from app.models.enums import ConstraintType, MovementContext

from app.models.base import AbstractAttributEntity

if TYPE_CHECKING:
    from app.models.flow import Flow
    from app.models.service_type import ServiceType



class Constraint(AbstractAttributEntity):
    """
    Flow constraint
    Equivalent to Constraint entity
    """
    __tablename__ = "flow_constraint"
    __table_args__ = (
        Index("idx_flow_constraint_code", "code"),
        Index("idx_flow_constraint_code_deleted", "code", "deleted"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    code: Mapped[ConstraintType] = mapped_column(Enum(ConstraintType))
    
    value: Mapped[str | None] = mapped_column(String)
    
    context: Mapped[MovementContext] = mapped_column(
        Enum(MovementContext),
        default=MovementContext.INITIATION
    )
    
    # Foreign Keys
    flow_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("flow.id")
    )
    
    service_type_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("service_type.id")
    )
    
    # Relationships
    flow: Mapped["Flow | None"] = relationship(
        "Flow",
        back_populates="constraints"
    )
    
    service_type: Mapped["ServiceType | None"] = relationship(
        "ServiceType",
        back_populates="constraints"
    )