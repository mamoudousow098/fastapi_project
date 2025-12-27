from sqlalchemy import String, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy import String, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.models.base import AbstractAttributEntity

if TYPE_CHECKING:
    from app.models.flow import Flow
    from app.models.impact_rule_type import ImpactRuleType
    from app.models.rule_account_role import RuleAccountRole
    from app.models.interval import Interval


class ImpactRule(AbstractAttributEntity):
    __tablename__ = "impact_rule"

    __table_args__ = (
        Index("idx_impact_rule_code", "code"),
        Index("idx_impact_rule_code_deleted", "code", "deleted"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    code: Mapped[str | None] = mapped_column(String)
    label: Mapped[str | None] = mapped_column(String)

    # ================= FOREIGN KEYS =================
    
    # ✅ @JoinColumn(name = "id_rule_account_role")
    rule_account_role_id: Mapped[int | None] = mapped_column(
        "rule_account_role_id",
        Integer, 
        ForeignKey("rule_account_role.id")
    )

    # ✅ @JoinColumn(name = "id_impact_rule_type")
    impact_rule_type_id: Mapped[int | None] = mapped_column(
        "impact_rule_type_id",
        Integer, 
        ForeignKey("impact_rule_type.id")
    )

    # ✅ @JoinColumn(name = "id_flow")
    flow_id: Mapped[int | None] = mapped_column(
        Integer, 
        ForeignKey("flow.id")
    )

    # ================= RELATIONS =================
    
    # ✅ @OneToMany(cascade = CascadeType.ALL, orphanRemoval = true)
    intervals: Mapped[list["Interval"]] = relationship(
        "Interval",
        cascade="all, delete-orphan",
        back_populates="impact_rule"
    )

    # ✅ @OneToOne(cascade = CascadeType.ALL, orphanRemoval = true)
    rule_account_role: Mapped["RuleAccountRole"] = relationship(
        "RuleAccountRole",
        cascade="all, delete-orphan",
        single_parent=True,
        uselist=False
    )

    # ✅ @ManyToOne
    impact_rule_type: Mapped["ImpactRuleType | None"] = relationship(
        "ImpactRuleType"
    )

    # ✅ @ManyToOne
    flow: Mapped["Flow | None"] = relationship(
        "Flow",
        back_populates="rules"
    )