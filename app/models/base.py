from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import event

from app.models.enums import EntityState


class Base(DeclarativeBase):
    pass


class AbstractAttributEntity(Base):
    __abstract__ = True

    creation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=datetime.utcnow
    )

    updated_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    status: Mapped[EntityState] = mapped_column(
        Enum(EntityState, name="entity_state"),
        nullable=False,
        default=EntityState.ACTIVE
    )


@event.listens_for(AbstractAttributEntity, "before_insert", propagate=True)
def pre_persist(mapper, connection, target):
    if target.creation_date is None:
        target.creation_date = datetime.utcnow()
    if target.updated_date is None:
        target.updated_date = datetime.utcnow()


@event.listens_for(AbstractAttributEntity, "before_update", propagate=True)
def pre_update(mapper, connection, target):
    target.updated_date = datetime.utcnow()
