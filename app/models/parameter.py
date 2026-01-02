from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


# ==================== Parameter Model ====================
class Parameter(Base):
    """
    Parameter model - stores system configuration parameters
    Equivalent to Java Parameter class

    Used for storing URLs, configuration values, and other system parameters
    """

    __tablename__ = "parametre"

    __table_args__ = (
        Index("idx_parameter_code", "prm_code"),
        Index("idx_parameter_code_status", "prm_code", "prm_statut"),
    )

    prm_id: Mapped[int] = mapped_column("prm_id", primary_key=True, autoincrement=True)
    prm_value: Mapped[int] = mapped_column("prm_value", default=1, nullable=False)
    prm_code: Mapped[str | None] = mapped_column("prm_code", String(255), nullable=True, index=True)
    prm_string_value: Mapped[str | None] = mapped_column("prm_stringvalue", String(1000), nullable=True)
    prm_statut: Mapped[int] = mapped_column("prm_statut", default=1, nullable=False)

    def __repr__(self):
        return (f"Parameter(prm_id={self.prm_id}, prm_code={self.prm_code}, "
                f"prm_value={self.prm_value}, prm_string_value={self.prm_string_value})")

    @property
    def is_active(self) -> bool:
        """Check if parameter is active"""
        return self.prm_statut == 1
