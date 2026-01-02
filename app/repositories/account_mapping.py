import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.parameter import Parameter
from app.models.service_mapping import ServiceMapping
from app.models.account_mapping import AccountMapping

logger = logging.getLogger(__name__)

# ==================== AccountMappingRepository ====================
class AccountMappingRepository:
    """Repository for AccountMapping entity"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_code_gu3(self, code_gu3: str) -> Optional[AccountMapping]:
        """
        Get account mapping by GU3 (internal) code

        Args:
            code_gu3: Internal account code

        Returns:
            AccountMapping if found, None otherwise
        """
        logger.debug(f"Getting account mapping by code_gu3: {code_gu3}")

        mapping = self.db.query(AccountMapping).filter(
            AccountMapping.code_gu3 == code_gu3,
            AccountMapping.deleted == False
        ).first()

        if mapping:
            logger.debug(f"Account mapping found: {code_gu3} -> {mapping.code_gu1}")
        else:
            logger.debug(f"Account mapping not found for code_gu3: {code_gu3}")

        return mapping

    def get_by_code_gu1(self, code_gu1: str) -> Optional[AccountMapping]:
        """
        Get account mapping by GU1 (external) code

        Args:
            code_gu1: External account code

        Returns:
            AccountMapping if found, None otherwise
        """
        logger.debug(f"Getting account mapping by code_gu1: {code_gu1}")

        mapping = self.db.query(AccountMapping).filter(
            AccountMapping.code_gu1 == code_gu1,
            AccountMapping.deleted == False
        ).first()

        if mapping:
            logger.debug(f"Account mapping found: {mapping.code_gu3} -> {code_gu1}")
        else:
            logger.debug(f"Account mapping not found for code_gu1: {code_gu1}")

        return mapping

    def get_by_id(self, mapping_id: int) -> Optional[AccountMapping]:
        """Get account mapping by ID"""
        return self.db.query(AccountMapping).filter(
            AccountMapping.id == mapping_id,
            AccountMapping.deleted == False
        ).first()

    def get_all(self) -> List[AccountMapping]:
        """Get all active account mappings"""
        return self.db.query(AccountMapping).filter(
            AccountMapping.deleted == False
        ).all()

    def get_by_account_type(self, account_type: str) -> List[AccountMapping]:
        """Get account mappings by account type"""
        return self.db.query(AccountMapping).filter(
            AccountMapping.account_type == account_type,
            AccountMapping.deleted == False
        ).all()

    def create(self, mapping: AccountMapping) -> AccountMapping:
        """Create a new account mapping"""
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        logger.info(f"Created account mapping: {mapping.code_gu3} -> {mapping.code_gu1}")
        return mapping

    def update(self, mapping: AccountMapping) -> AccountMapping:
        """Update an existing account mapping"""
        mapping.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(mapping)
        logger.info(f"Updated account mapping: {mapping.code_gu3} -> {mapping.code_gu1}")
        return mapping

    def delete(self, mapping_id: int) -> bool:
        """Soft delete an account mapping"""
        mapping = self.get_by_id(mapping_id)
        if mapping:
            mapping.deleted = True
            mapping.updated_at = datetime.now()
            self.db.commit()
            logger.info(f"Deleted account mapping: {mapping.code_gu3} -> {mapping.code_gu1}")
            return True
        return False