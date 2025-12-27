from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from app.models.base import AbstractAttributEntity
from app.models.country import Country

if TYPE_CHECKING:
    from app.models.account import Account


class LegalEntity(AbstractAttributEntity):
    __tablename__ = "legal_entity"

    id: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str] = mapped_column(String)
    label: Mapped[str] = mapped_column(String)
    address: Mapped[str | None] = mapped_column(String)
    ninea: Mapped[str | None] = mapped_column(String)

    phone_contact: Mapped[str | None] = mapped_column(String)
    email_contact: Mapped[str | None] = mapped_column(String)
    name_contact: Mapped[str | None] = mapped_column(String)
    reference_odoo: Mapped[str | None] = mapped_column(String)

    country_id: Mapped[str | None] = mapped_column(
        ForeignKey("country.iso_code")
    )
    country: Mapped[Country] = relationship()
    
    # ✅ Ajoutez cette relation pour correspondre au back_populates dans Account
    accounts: Mapped[list["Account"]] = relationship(
        "Account", 
        back_populates="legal_entity"
    )

    services: Mapped[list["Service"]] = relationship(
        "Service",
        back_populates="legal_entity"
    )