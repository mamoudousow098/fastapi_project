"""
Supporting services for external call handler
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models.service_mapping import ServiceMapping
from app.models.parameter import Parameter
from app.models.status import Status
from app.models.enums import StatusEnum

logger = logging.getLogger(__name__)


class ServiceMappingService:
    """Service for managing service mappings between GU3 and GU1"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_code_gu3(self, code_gu3: str) -> Optional[ServiceMapping]:
        """
        Get service mapping by GU3 code

        Args:
            code_gu3: The GU3 service code

        Returns:
            ServiceMapping if found, None otherwise
        """
        logger.info(f"Finding service mapping for code_gu3: {code_gu3}")

        mapping = self.db.query(ServiceMapping).filter(
            ServiceMapping.code_gu3 == code_gu3,
            ServiceMapping.deleted == False
        ).first()

        if mapping:
            logger.info(f"Service mapping found: {code_gu3} -> {mapping.code_gu1}")
        else:
            logger.warning(f"No service mapping found for code_gu3: {code_gu3}")

        return mapping

    def get_by_code_gu1(self, code_gu1: str) -> Optional[ServiceMapping]:
        """
        Get service mapping by GU1 code

        Args:
            code_gu1: The GU1 service code

        Returns:
            ServiceMapping if found, None otherwise
        """
        logger.info(f"Finding service mapping for code_gu1: {code_gu1}")

        mapping = self.db.query(ServiceMapping).filter(
            ServiceMapping.code_gu1 == code_gu1,
            ServiceMapping.deleted == False
        ).first()

        if mapping:
            logger.info(f"Service mapping found: {mapping.code_gu3} -> {code_gu1}")
        else:
            logger.warning(f"No service mapping found for code_gu1: {code_gu1}")

        return mapping

    def get_all_mappings(self) -> list[ServiceMapping]:
        """Get all active service mappings"""
        return self.db.query(ServiceMapping).filter(
            ServiceMapping.deleted == False
        ).all()
