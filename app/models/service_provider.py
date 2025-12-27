from sqlalchemy import String, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AbstractAttributEntity


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

    flow = relationship(
        "Flow",
        back_populates="provider"
    )
