from datetime import datetime
from sqlalchemy import String, Integer, Boolean, ForeignKey, Enum, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY

from app.models.base import AbstractAttributEntity, Base
from app.models.enums import AccountCategory
from app.models.account_dependency import *
from app.models.legal_entity import LegalEntity
from app.models.country import Country

# Association table for ManyToMany with AccountType
# ✅ Utilisez Column() au lieu de mapped_column() pour les tables d'association
account_account_type = Table(
    "account_account_type",
    Base.metadata,  # ← Utilisez Base.metadata au lieu de AbstractAttributEntity.metadata
    Column("id_account", Integer, ForeignKey("account.id"), primary_key=True),
    Column("id_account_type", Integer, ForeignKey("account_type.id"), primary_key=True),
)

class Account(AbstractAttributEntity):
    __tablename__ = "account"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_number: Mapped[str | None] = mapped_column(String, unique=True)
    phone_number: Mapped[str | None] = mapped_column(String)
    label: Mapped[str | None] = mapped_column(String)
    merchant_code: Mapped[str | None] = mapped_column(String, unique=True)
    reference_odoo: Mapped[str | None] = mapped_column(String)

    # --- ManyToOne ---
    legal_entity_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("legal_entity.id"))
    legal_entity: Mapped["LegalEntity"] = relationship("LegalEntity", back_populates="accounts")

    client_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("client.id"))
    client: Mapped["Client"] = relationship("Client", back_populates="accounts")

    bank_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("bank.id"))
    bank: Mapped["Bank"] = relationship("Bank", back_populates="accounts")

    country_id: Mapped[str | None] = mapped_column(String, ForeignKey("country.iso_code"))
    country: Mapped["Country"] = relationship("Country", back_populates="accounts")

    category: Mapped[AccountCategory | None] = mapped_column(Enum(AccountCategory))

    identification_system: Mapped[str | None] = mapped_column(String)
    identification_number: Mapped[str | None] = mapped_column(String)
    devise: Mapped[str | None] = mapped_column(String)
    RCCM_client_number: Mapped[str | None] = mapped_column(String)
    overdraft_activated: Mapped[bool | None] = mapped_column(Boolean)

    # Self reference ManyToOne (parent account)
    parent_account_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("account.id"))
    account: Mapped["Account"] = relationship("Account", remote_side=[id], foreign_keys=[parent_account_id])

    # --- ManyToMany ---
    account_types: Mapped[list["AccountType"]] = relationship(
        "AccountType",
        secondary=account_account_type,
        back_populates="accounts"
    )

    # --- OneToOne ---
    #balance_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("balance.id"))
    #balance: Mapped["Balance"] = relationship("Balance", uselist=False, cascade="all, delete-orphan")

    # --- OneToOne ---
    balance_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("balance.id"))
    balance: Mapped["Balance"] = relationship(
        "Balance", 
        uselist=False,  
        cascade="all, delete-orphan",
        single_parent=True  # ✅ Ajoutez ceci pour delete-orphan sur OneToOne
    )

    # --- Arrays / Sets ---
    kyc_levels: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    EME_account_number: Mapped[str | None] = mapped_column(String)
    principal_distri_account_number: Mapped[str | None] = mapped_column(String)

    provider_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("provider.id"))
    provider: Mapped["Provider"] = relationship("Provider", back_populates="accounts")

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False)

    # --- Helper methods ---
    def is_provider(self) -> bool:
        if self.account_types:
            codes = [at.code for at in self.account_types]
            return any(c in ["EXT_COM_DISTRI", "EXT_NOM_DISTRI", "PI_EME"] for c in codes)
        return False

    def is_mirror_bank(self) -> bool:
        if self.account_types:
            codes = [at.code for at in self.account_types]
            return any(c in ["CMS_EME", "COM_EME"] for c in codes)
        return False

    def is_nominal_provider(self) -> bool:
        if self.account_types:
            codes = [at.code for at in self.account_types]
            return "EXT_NOM_DISTRI" in codes
        return False

    def is_commission_provider(self) -> bool:
        if self.account_types:
            codes = [at.code for at in self.account_types]
            return "EXT_COM_DISTRI" in codes
        return False