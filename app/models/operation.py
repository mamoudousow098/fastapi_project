from datetime import datetime
from typing import Dict, Any

from sqlalchemy import String, Integer, Float, DateTime, Enum, Index, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import OperationDirection


class Operation(Base):
    __tablename__ = "operation"
    __table_args__ = (
        UniqueConstraint(
            "amount",
            "account_number",
            "gu_id",
            "impact_rule_code",
            name="UniqueAmountAccountNumberGuIDImpactRuleCode"
        ),
        Index("idx_gu_id_op", "gu_id"),
        Index("index_op_date", "op_date"),
        Index("index_account_number", "account_number"),
        Index("index_impact_rule_code", "impact_rule_code"),
        Index("idx_composite_accountNumber_opDate", "account_number", "op_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Amount and balances
    amount: Mapped[float | None] = mapped_column(Float)
    balance_before: Mapped[float | None] = mapped_column(Float)
    balance_after: Mapped[float | None] = mapped_column(Float)

    # Account information
    account_number: Mapped[str | None] = mapped_column(String)
    account_label: Mapped[str | None] = mapped_column(String)
    super_account_number: Mapped[str | None] = mapped_column(String)
    account_role: Mapped[str | None] = mapped_column(String)

    # Identifiers
    gu_id: Mapped[str | None] = mapped_column(String)
    balance_id: Mapped[int | None] = mapped_column(Integer, name="id_balance")

    # Operation details
    operation_direction: Mapped[OperationDirection | None] = mapped_column(
        Enum(OperationDirection, name="operation_direction_enum"),
        name="sens_operation"
    )
    op_date: Mapped[datetime | None] = mapped_column(DateTime)

    # Entity and product
    legal_entity_code: Mapped[str | None] = mapped_column(String)
    product_code: Mapped[str | None] = mapped_column(String)

    # Commissions and fees
    global_commission: Mapped[float | None] = mapped_column(Float, name="global_comission")
    global_fees: Mapped[float | None] = mapped_column(Float)
    issuer_commissions: Mapped[float | None] = mapped_column(Float)
    acquirer_commissions: Mapped[float | None] = mapped_column(Float)
    issuer_fees: Mapped[float | None] = mapped_column(Float, name="issuer_charges")
    acquirer_fees: Mapped[float | None] = mapped_column(Float, name="acquirer_charges")

    # Impact rule
    impact_rule_code: Mapped[str | None] = mapped_column(String)

    # User and partner information
    user_login: Mapped[str | None] = mapped_column(String)
    partner_dist_id: Mapped[str | None] = mapped_column(String)
    partner_id: Mapped[str | None] = mapped_column(String)

    # Optional: Relationship to Movement (if you want bidirectional linking)
    # movement: Mapped["Movement"] = relationship(
    #     "Movement",
    #     foreign_keys="[Operation.gu_id]",
    #     primaryjoin="Operation.gu_id == Movement.gu_id",
    #     back_populates="operations"
    # )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Operation object to dictionary for JSON serialization

        Returns:
            Dictionary representation of the operation
        """
        return {
            "id": self.id,
            "amount": self.amount,
            "balance_before": self.balance_before,
            "balance_after": self.balance_after,
            "account_number": self.account_number,
            "account_label": self.account_label,
            "super_account_number": self.super_account_number,
            "account_role": self.account_role,
            "gu_id": self.gu_id,
            "balance_id": self.balance_id,
            "operation_direction": self.operation_direction.value if self.operation_direction else None,
            "op_date": self.op_date.isoformat() if self.op_date else None,
            "legal_entity_code": self.legal_entity_code,
            "product_code": self.product_code,
            "global_commission": self.global_commission,
            "global_fees": self.global_fees,
            "issuer_commissions": self.issuer_commissions,
            "acquirer_commissions": self.acquirer_commissions,
            "issuer_fees": self.issuer_fees,
            "acquirer_fees": self.acquirer_fees,
            "impact_rule_code": self.impact_rule_code,
            "user_login": self.user_login,
            "partner_dist_id": self.partner_dist_id,
            "partner_id": self.partner_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Operation":
        """
        Create Operation object from dictionary

        Args:
            data: Dictionary containing operation data

        Returns:
            Operation instance
        """
        operation = cls()

        # Simple fields
        for field in [
            "id", "amount", "balance_before", "balance_after",
            "account_number", "account_label", "super_account_number", "account_role",
            "gu_id", "balance_id", "legal_entity_code", "product_code",
            "global_commission", "global_fees", "issuer_commissions", "acquirer_commissions",
            "issuer_fees", "acquirer_fees", "impact_rule_code",
            "user_login", "partner_dist_id", "partner_id"
        ]:
            if field in data:
                setattr(operation, field, data[field])

        # Handle enum
        if "operation_direction" in data and data["operation_direction"]:
            operation.operation_direction = OperationDirection(data["operation_direction"])

        # Handle datetime
        if "op_date" in data and data["op_date"]:
            if isinstance(data["op_date"], str):
                operation.op_date = datetime.fromisoformat(data["op_date"])
            else:
                operation.op_date = data["op_date"]

        return operation