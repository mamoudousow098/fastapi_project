from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.impact_rule import ImpactRule


class Interval(Base):
    __tablename__ = "interval_rule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    minimum_amount: Mapped[float] = mapped_column("min_amount", Float)
    maximum_amount: Mapped[float] = mapped_column("max_amount", Float)

    percentage: Mapped[float | None] = mapped_column(Float)
    fixe: Mapped[float | None] = mapped_column(Float)

    # ✅ Foreign key vers ImpactRule
    impact_rule_id: Mapped[int] = mapped_column(
        "impact_rule_id",  # Nom de colonne cohérent avec Java
        Integer,
        ForeignKey("impact_rule.id"),
        nullable=False
    )

    # ✅ Relation back vers ImpactRule
    impact_rule: Mapped["ImpactRule"] = relationship(
        "ImpactRule",
        back_populates="intervals"
    )

    # ==== business method ====
    def can_interval_support_amount(self, amount: float) -> bool:
        return self.minimum_amount <= amount <= self.maximum_amount