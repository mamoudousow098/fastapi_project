# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.core.config import settings
from app.models.base import Base  # Import Base depuis models.base

# ✅ IMPORTEZ TOUS VOS MODÈLES ICI
from app.models.user import User
from app.models.account import Account
from app.models.account_dependency import *
from app.models.constraint import Constraint
from app.models.country import Country
from app.models.flow import Flow
from app.models.impact_rule import ImpactRule
from app.models.impact_rule_type import ImpactRuleType
from app.models.interval import Interval
from app.models.legal_entity import LegalEntity
from app.models.rule_account_role import RuleAccountRole
from app.models.service import Service
from app.models.service_provider import ServiceProvider
from app.models.service_type import ServiceType
from app.models.movement import Movement
from app.models.operation import Operation
from app.models.product import  Product
from app.models.service_operator import ServiceOperator
from app.models.account_role import AccountRole
from app.models.status import Status
from app.models.history_mvt_status import HistoryMvtStatus

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()