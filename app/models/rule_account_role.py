from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from typing import TYPE_CHECKING

from app.models.base import Base
if TYPE_CHECKING:
    from app.models.impact_rule import ImpactRule



class RuleAccountRole(Base):
    __tablename__ = "rule_account_role"

    id: Mapped[int] = mapped_column(primary_key=True)

    role_identifier: Mapped[str] = mapped_column(String)

    account_types: Mapped[list[str] | None] = mapped_column(
        "account_types",
        ARRAY(String),
        nullable=True
    )


   
    # impact_rule = relationship(
    #     "ImpactRule",
    #     back_populates="rule_account_role",
    #     uselist=False
    # )
