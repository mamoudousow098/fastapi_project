# from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
# from sqlalchemy import func
# from datetime import datetime


# class Base(DeclarativeBase):
#     """Classe de base pour tous les modèles SQLAlchemy"""
#     pass


# class TimestampMixin:
#     """
#     Mixin pour ajouter automatiquement created_at et updated_at
#     Usage: class User(Base, TimestampMixin):
#     """
#     created_at: Mapped[datetime] = mapped_column(
#         default=func.now(),
#         nullable=False,
#         comment="Date de création"
#     )
    
#     updated_at: Mapped[datetime] = mapped_column(
#         default=func.now(),
#         onupdate=func.now(),
#         nullable=False,
#         comment="Date de dernière modification"
#     )

# app/db/base.py
from app.models.base import Base

__all__ = ["Base"]