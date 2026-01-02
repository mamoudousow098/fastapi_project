# ==================== ServiceMappingRepository ====================
import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.parameter import Parameter
from app.models.service_mapping import ServiceMapping
from app.models.account_mapping import AccountMapping

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session

from app.models.service_mapping import ServiceMapping


class ServiceMappingRepository:
    """Repository for ServiceMapping entity"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_code_gu3(self, code_gu3: str) -> Optional[ServiceMapping]:
        """
        Get service mapping by GU3 (internal) code

        Args:
            code_gu3: Internal service code

        Returns:
            ServiceMapping if found, None otherwise
        """
        logger.debug(f"Getting service mapping by code_gu3: {code_gu3}")

        mapping = self.db.query(ServiceMapping).filter(
            ServiceMapping.code_gu3 == code_gu3,
            ServiceMapping.deleted == False
        ).first()

        if mapping:
            logger.debug(f"Service mapping found: {code_gu3} -> {mapping.code_gu1}")
        else:
            logger.debug(f"Service mapping not found for code_gu3: {code_gu3}")

        return mapping

    def get_by_code_gu1(self, code_gu1: str) -> Optional[ServiceMapping]:
        """
        Get service mapping by GU1 (external) code

        Args:
            code_gu1: External service code

        Returns:
            ServiceMapping if found, None otherwise
        """
        logger.debug(f"Getting service mapping by code_gu1: {code_gu1}")

        mapping = self.db.query(ServiceMapping).filter(
            ServiceMapping.code_gu1 == code_gu1,
            ServiceMapping.deleted == False
        ).first()

        if mapping:
            logger.debug(f"Service mapping found: {mapping.code_gu3} -> {code_gu1}")
        else:
            logger.debug(f"Service mapping not found for code_gu1: {code_gu1}")

        return mapping

    def get_by_id(self, mapping_id: int) -> Optional[ServiceMapping]:
        """Get service mapping by ID"""
        return self.db.query(ServiceMapping).filter(
            ServiceMapping.id == mapping_id,
            ServiceMapping.deleted == False
        ).first()

    def get_all(self) -> List[ServiceMapping]:
        """Get all active service mappings"""
        return self.db.query(ServiceMapping).filter(
            ServiceMapping.deleted == False
        ).all()

    def create(self, mapping: ServiceMapping) -> ServiceMapping:
        """Create a new service mapping"""
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        logger.info(f"Created service mapping: {mapping.code_gu3} -> {mapping.code_gu1}")
        return mapping

    def update(self, mapping: ServiceMapping) -> ServiceMapping:
        """Update an existing service mapping"""
        mapping.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(mapping)
        logger.info(f"Updated service mapping: {mapping.code_gu3} -> {mapping.code_gu1}")
        return mapping

    def delete(self, mapping_id: int) -> bool:
        """Soft delete a service mapping"""
        mapping = self.get_by_id(mapping_id)
        if mapping:
            mapping.deleted = True
            mapping.updated_at = datetime.now()
            self.db.commit()
            logger.info(f"Deleted service mapping: {mapping.code_gu3} -> {mapping.code_gu1}")
            return True
        return False
