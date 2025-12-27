from sqlalchemy import String, Integer, Index, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY

from app.models.base import AbstractAttributEntity


class Product(AbstractAttributEntity):
    """Modèle Product - Produit financier"""
    __tablename__ = "product"
    __table_args__ = (
        Index("idx_product_codep", "code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    code: Mapped[str | None] = mapped_column(String)
    label: Mapped[str | None] = mapped_column(String)
    
    # Set<String> en Java devient ARRAY(String) en PostgreSQL
    kyc_levels: Mapped[list[str] | None] = mapped_column(ARRAY(String))