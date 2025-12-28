from sqlalchemy import String, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import AbstractAttributEntity
from app.models.enums import MovementTypeEnum
# ❌ SUPPRIMEZ CETTE LIGNE : from app.models.service import Service
# ❌ SUPPRIMEZ AUSSI : from app.models.constraint import Constraint (si circulaire)


class ServiceType(AbstractAttributEntity):
    __tablename__ = "service_type"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    code: Mapped[str] = mapped_column(String)
    short_code: Mapped[str | None] = mapped_column(String)
    label: Mapped[str] = mapped_column(String)

    movement_type: Mapped[MovementTypeEnum] = mapped_column(
        Enum(MovementTypeEnum)
    )

    # ✅ Utilisez la string "Service" au lieu d'importer la classe
    services: Mapped[list["Service"]] = relationship(
        "Service",  # ← String au lieu de classe
        back_populates="service_type"
    )

    # ✅ Utilisez la string "Constraint"
    constraints: Mapped[list["Constraint"]] = relationship(
        "Constraint",
        back_populates="service_type"
    )