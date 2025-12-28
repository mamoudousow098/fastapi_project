from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Enum, Index, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSON

from app.models.base import AbstractAttributEntity
from app.models.enums import MovementTypeEnum


class Movement(AbstractAttributEntity):
    __tablename__ = "movement"
    __table_args__ = (
        Index("idx_status_code", "status_code"),
        Index("index_creation_date", "creation_date"),
        Index("idx_gu_id", "gu_id"),
        Index("idx_user_login", "user_login"),
        Index("idx_product_code", "product_code"),
        Index("idx_service_code", "service_code"),
        Index("idx_client_id", "client_id"),
        Index("idx_partner_id", "partner_id"),
        Index("idx_legal_entity_code", "legal_entity_code"),
        Index("idx_merchant_code", "merchant_code"),
        Index("idx_issuer_account", "issuer_account"),
        Index("idx_reference_bulk", "reference_bulk"),
        Index("idx_agent_login", "agent_login"),
        Index("idx_partner_dist_id", "partner_dist_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Flow information
    flow_code: Mapped[str | None] = mapped_column(String)
    flow_version: Mapped[str | None] = mapped_column(String)

    # Amounts and dates
    amount: Mapped[float | None] = mapped_column(Float)
    impact_date: Mapped[datetime | None] = mapped_column(DateTime)
    sent_date: Mapped[datetime | None] = mapped_column(DateTime)
    cancellation_date: Mapped[datetime | None] = mapped_column(DateTime)
    end_date: Mapped[datetime | None] = mapped_column(DateTime)

    # Commissions and fees
    global_commission: Mapped[float | None] = mapped_column(Float)
    global_fees: Mapped[float | None] = mapped_column(Float)
    issuer_commissions: Mapped[float | None] = mapped_column(Float)
    acquirer_commissions: Mapped[float | None] = mapped_column(Float)
    issuer_fees: Mapped[float | None] = mapped_column(Float, name="issuer_charges")
    acquirer_fees: Mapped[float | None] = mapped_column(Float, name="acquirer_charges")
    issuer_impact: Mapped[float | None] = mapped_column(Float)
    acquirer_impact: Mapped[float | None] = mapped_column(Float)
    commission_base: Mapped[float | None] = mapped_column(Float)
    charge_base: Mapped[float | None] = mapped_column(Float)

    # Identifiers
    gu_id: Mapped[str | None] = mapped_column(String, unique=True)
    partner_id: Mapped[str | None] = mapped_column(String)
    partner_dist_id: Mapped[str | None] = mapped_column(String)
    client_id: Mapped[str | None] = mapped_column(String)
    merchant_code: Mapped[str | None] = mapped_column(String)
    legal_entity_code: Mapped[str | None] = mapped_column(String)
    bank_code: Mapped[str | None] = mapped_column(String)
    terminal_id: Mapped[str | None] = mapped_column(String)
    log_id: Mapped[str | None] = mapped_column(String)

    # Geographic information
    country_iso_code: Mapped[str | None] = mapped_column(String)
    latitude: Mapped[str | None] = mapped_column(String)
    longitude: Mapped[str | None] = mapped_column(String)

    # User information
    user_login: Mapped[str | None] = mapped_column(String)
    agent_login: Mapped[str | None] = mapped_column(String)
    user_agent: Mapped[str | None] = mapped_column(String)

    # Service information
    product_code: Mapped[str | None] = mapped_column(String)
    service_code: Mapped[str | None] = mapped_column(String)
    service_label: Mapped[str | None] = mapped_column(String)
    service_type_code: Mapped[str | None] = mapped_column(String)

    # Accounts
    issuer_account: Mapped[str | None] = mapped_column(String)
    acquirer_account: Mapped[str | None] = mapped_column(String)
    issuer_account_label: Mapped[str | None] = mapped_column(String)
    acquirer_account_label: Mapped[str | None] = mapped_column(String)
    super_issuer: Mapped[str | None] = mapped_column(String)
    super_acquirer: Mapped[str | None] = mapped_column(String)

    # Status and messages
    status_code: Mapped[str | None] = mapped_column(String)
    message: Mapped[str | None] = mapped_column(String)
    reject_reason: Mapped[str | None] = mapped_column(String)
    cancellation_reason: Mapped[str | None] = mapped_column(String)
    reason: Mapped[str | None] = mapped_column(String)

    # References
    reference_bulk: Mapped[str | None] = mapped_column(String)
    slip_number: Mapped[str | None] = mapped_column(String)
    callback_url: Mapped[str | None] = mapped_column(String)

    # Other
    other_participant_code: Mapped[str | None] = mapped_column(String)
    operator: Mapped[str | None] = mapped_column(String)
    tag: Mapped[str | None] = mapped_column(String)
    change_tag: Mapped[str | None] = mapped_column(String)

    # Enum
    movement_type: Mapped[MovementTypeEnum | None] = mapped_column(
        Enum(MovementTypeEnum, name="movement_type_enum")
    )

    # JSON columns (stored as JSON in PostgreSQL)
    load_operations: Mapped[dict | None] = mapped_column(JSON)
    cancel_operations: Mapped[dict | None] = mapped_column(JSON)
    account_roles: Mapped[dict | None] = mapped_column(JSON)
    additional_informations: Mapped[dict | None] = mapped_column(JSON)
