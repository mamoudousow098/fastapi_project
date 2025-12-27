from sqlalchemy import String, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column
from typing import TYPE_CHECKING

from app.models.base import AbstractAttributEntity

# ❌ PAS DE RELATION - ImpactRuleType n'a pas de @OneToMany en Java


class ImpactRuleType(AbstractAttributEntity):
    __tablename__ = "impact_rule_type"
    
    __table_args__ = (
        Index("idx_impact_rule_type_code", "code"),
        Index("idx_impact_rule_type_code_deleted", "code", "deleted"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    code: Mapped[str | None] = mapped_column(String)
    label: Mapped[str | None] = mapped_column(String)
    
    # ❌ PAS DE RELATION impact_rules ici