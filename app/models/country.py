from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.models.base import AbstractAttributEntity

if TYPE_CHECKING:
    from app.models.account import Account


class Country(AbstractAttributEntity):
    __tablename__ = "country"

    iso_code: Mapped[str] = mapped_column(String, primary_key=True)

    currency: Mapped[str | None] = mapped_column(String)
    phone_number_length: Mapped[str | None] = mapped_column(String)
    language: Mapped[str | None] = mapped_column(String)
    timezone: Mapped[str | None] = mapped_column(String)
    spoc_number: Mapped[str | None] = mapped_column(String)
    country_name: Mapped[str | None] = mapped_column(String)
    area_code: Mapped[int | None] = mapped_column(Integer)
    currency_number: Mapped[str | None] = mapped_column(String)

    # ✅ Ajoutez cette relation
    accounts: Mapped[list["Account"]] = relationship(
        "Account", 
        back_populates="country"
    )