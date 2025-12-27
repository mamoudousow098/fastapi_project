from sqlalchemy import String, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.models.base import AbstractAttributEntity
from app.models.enums import ServiceFlow, ServiceScope

if TYPE_CHECKING:
    from app.models.service_type import ServiceType
    from app.models.legal_entity import LegalEntity
    from app.models.service_operator import ServiceOperator


class Service(AbstractAttributEntity):
    __tablename__ = "service"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    code: Mapped[str] = mapped_column(String)
    label: Mapped[str] = mapped_column(String)

    service_flow: Mapped[ServiceFlow] = mapped_column(Enum(ServiceFlow))
    scope: Mapped[ServiceScope] = mapped_column(
        Enum(ServiceScope), default=ServiceScope.INTERNAL
    )

    # ✅ Foreign Keys
    service_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("service_type.id")
    )
    legal_entity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("legal_entity.id")
    )
    service_operator_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("operator.id")
    )

    # ✅ Relationships
    service_type: Mapped["ServiceType"] = relationship(
        "ServiceType",
        back_populates="services"
    )
    
    legal_entity: Mapped["LegalEntity"] = relationship(
        "LegalEntity",
        back_populates="services"
    )
    
    operator: Mapped["ServiceOperator | None"] = relationship(
        "ServiceOperator",
        back_populates="services"
    )