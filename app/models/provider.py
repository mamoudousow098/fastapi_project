# ==================== Provider Model ====================
from sqlalchemy import Index, String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.models import AbstractAttributEntity

if TYPE_CHECKING:
    from app.models.service_provider import ServiceProvider
    from app.models.account import Account


# class Provider(AbstractAttributEntity):
#     """
#     Provider entity - represents external service providers
#     Equivalent to Java Provider class
#     """
#
#     __tablename__ = "provider"
#
#     __table_args__ = (
#         Index("idx_provider_code", "code"),
#         Index("idx_provider_code_deleted", "code", "deleted"),
#     )
#
#     id: Mapped[int] = mapped_column(primary_key=True)
#     code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
#     label: Mapped[str | None] = mapped_column(String(255), nullable=True)
#
#     def __repr__(self):
#         return f"Provider(id={self.id}, code={self.code}, label={self.label})"
# ==================== Provider Model ====================
class Provider(AbstractAttributEntity):
    """
    Provider entity - represents external service providers
    Equivalent to Java Provider class

    A provider is an external partner/vendor that provides services
    (e.g., Orange Money, Wave, Free Money, etc.)
    """

    __tablename__ = "provider"

    __table_args__ = (
        Index("idx_provider_code", "code"),
        Index("idx_provider_code_deleted", "code", "deleted"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    # One provider can have many service_providers (for different flows)
    service_providers: Mapped[list["ServiceProvider"]] = relationship(
        "ServiceProvider",
        back_populates="provider",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"Provider(id={self.id}, code={self.code}, label={self.label})"

    accounts: Mapped[list["Account"]] = relationship("Account", back_populates="provider")



