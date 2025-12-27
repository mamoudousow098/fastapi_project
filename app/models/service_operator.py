from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.models.base import AbstractAttributEntity

if TYPE_CHECKING:
    from app.models.service import Service


class ServiceOperator(AbstractAttributEntity):
    __tablename__ = "operator"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    short_code: Mapped[str | None] = mapped_column(String)
    label: Mapped[str | None] = mapped_column(String)
    
    # ✅ Relation OneToMany vers Service
    services: Mapped[list["Service"]] = relationship(
        "Service",
        back_populates="operator"
    )