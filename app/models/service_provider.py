from sqlalchemy import String, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.models.base import AbstractAttributEntity
if TYPE_CHECKING:
    from app.models.provider import Provider


class ServiceProvider(AbstractAttributEntity):
    __tablename__ = "service_provider"

    id: Mapped[int] = mapped_column(primary_key=True)

    provider_id: Mapped[int] = mapped_column(
        ForeignKey("provider.id"),
        nullable=False
    )

    flow_id: Mapped[int] = mapped_column(
        ForeignKey("flow.id"),
        nullable=False,
        unique=True
    )

    ranking: Mapped[int | None]
    url: Mapped[str | None] = mapped_column(String)

    gateway: Mapped[str | None] = mapped_column(String)

    # Relationships
    # Many-to-one: Many service_providers can reference one provider
    provider: Mapped["Provider"] = relationship(
        "Provider",
        back_populates="service_providers",
        lazy="joined"  # Equivalent to EAGER in Java
    )

    # One-to-one: One service_provider belongs to one flow
    flow: Mapped["Flow"] = relationship(
        "Flow",
        back_populates="provider",
        lazy="select"  # Equivalent to LAZY in Java
    )

    def __repr__(self):
        return (f"ServiceProvider(id={self.id}, provider_code={self.provider.code if self.provider else None}, "
                f"url={self.url}, gateway={self.gateway})")

