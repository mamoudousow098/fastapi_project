from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Enum, Index, Text, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AbstractAttributEntity, Base
from app.models.enums import AccountCategory, AccountPrefix

# --- ENTITIES ---
class Client(AbstractAttributEntity):
    __tablename__ = "client"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str | None] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String)
    address: Mapped[str | None] = mapped_column(String)
    notification_url: Mapped[str | None] = mapped_column(String)
    business_area: Mapped[str | None] = mapped_column(String)
    social_reason: Mapped[str | None] = mapped_column(String)
    client_type: Mapped[str | None] = mapped_column(String)
    client_category: Mapped[str | None] = mapped_column(String)
    client_status: Mapped[str | None] = mapped_column(String)
    is_activated: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    postal_code: Mapped[str | None] = mapped_column(String)
    photo: Mapped[str | None] = mapped_column(String)

    accounts: Mapped[list["Account"]] = relationship("Account", back_populates="client")


class Bank(AbstractAttributEntity):
    __tablename__ = "bank"
    __table_args__ = (
        Index("idx_bank_code", "code"),
        Index("idx_bank_code_deleted", "code", "deleted"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str | None] = mapped_column(String)
    name: Mapped[str | None] = mapped_column(String)
    country_iso_code: Mapped[str | None] = mapped_column(String)
    label: Mapped[str | None] = mapped_column(String)
    reference_odoo: Mapped[str | None] = mapped_column(String)

    accounts: Mapped[list["Account"]] = relationship("Account", back_populates="bank")


class AccountType(AbstractAttributEntity):
    __tablename__ = "account_type"
    __table_args__ = (
        Index("idx_account_type_code", "code"),
        Index("idx_account_type_code_deleted", "code", "deleted"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str | None] = mapped_column(String)
    label: Mapped[str | None] = mapped_column(String)
    category: Mapped[AccountCategory | None] = mapped_column(Enum(AccountCategory))
    prefix: Mapped[AccountPrefix | None] = mapped_column(Enum(AccountPrefix))

    accounts: Mapped[list["Account"]] = relationship(
        "Account",
        secondary="account_account_type",
        back_populates="account_types"
    )


class Provider(AbstractAttributEntity):
    __tablename__ = "provider"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str | None] = mapped_column(String)
    label: Mapped[str | None] = mapped_column(String)

    accounts: Mapped[list["Account"]] = relationship("Account", back_populates="provider")


class Balance(Base):
    __tablename__ = "balance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    last_updated_date: Mapped[datetime | None] = mapped_column(DateTime)
    last_updated_amount: Mapped[float] = mapped_column(Float, default=0.0)
    overdraft_amount: Mapped[float] = mapped_column(Float, default=0.0)