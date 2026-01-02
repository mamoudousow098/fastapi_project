"""
Supporting service classes for parameter and account mapping
"""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.account_mapping import AccountMapping
from app.repositories.account_mapping import AccountMappingRepository
from app.services.movement_checker import BrokerException

#from app.exceptions import BrokerException, MessagesEnum

logger = logging.getLogger(__name__)


# ==================== AccountMappingService ====================
class AccountMappingService:
    """
    Service for managing account mappings between internal and external codes
    Equivalent to Java AccountMappingService
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = AccountMappingRepository(db)

    def get_by_code_gu3(self, code_gu3: str) -> Optional[AccountMapping]:
        """
        Get account mapping by internal (GU3) code

        Args:
            code_gu3: Internal account code

        Returns:
            AccountMapping if found, None otherwise
        """
        logger.info(f"Getting account mapping by code_gu3: {code_gu3}")
        return self.repository.get_by_code_gu3(code_gu3)

    def get_by_code_gu1(self, code_gu1: str) -> Optional[AccountMapping]:
        """
        Get account mapping by external (GU1) code

        Args:
            code_gu1: External account code

        Returns:
            AccountMapping if found, None otherwise
        """
        logger.info(f"Getting account mapping by code_gu1: {code_gu1}")
        return self.repository.get_by_code_gu1(code_gu1)

    def get_by_id(self, mapping_id: int) -> Optional[AccountMapping]:
        """Get account mapping by ID"""
        return self.repository.get_by_id(mapping_id)

    def get_all_mappings(self) -> List[AccountMapping]:
        """Get all active account mappings"""
        return self.repository.get_all()

    def get_by_account_type(self, account_type: str) -> List[AccountMapping]:
        """Get account mappings by account type"""
        return self.repository.get_by_account_type(account_type)

    def create_mapping(
            self,
            code_gu3: str,
            code_gu1: str,
            account_type: Optional[str] = None
    ) -> AccountMapping:
        """
        Create a new account mapping

        Args:
            code_gu3: Internal account code
            code_gu1: External account code
            account_type: Account type (optional)

        Returns:
            Created AccountMapping

        Raises:
            BrokerException: If mapping already exists
        """
        logger.info(f"Creating account mapping: {code_gu3} -> {code_gu1}")

        # Check if mapping already exists
        existing = self.repository.get_by_code_gu3(code_gu3)
        if existing:
            raise BrokerException(
                "MessagesEnum.ACCOUNT_MAPPING_ALREADY_EXISTS",
                f"Account mapping for '{code_gu3}' already exists"
            )

        mapping = AccountMapping(
            code_gu3=code_gu3,
            code_gu1=code_gu1,
            account_type=account_type
        )

        return self.repository.create(mapping)

    def update_mapping(
            self,
            mapping_id: int,
            code_gu1: Optional[str] = None,
            account_type: Optional[str] = None
    ) -> AccountMapping:
        """
        Update an existing account mapping

        Args:
            mapping_id: Mapping ID
            code_gu1: New external code (optional)
            account_type: New account type (optional)

        Returns:
            Updated AccountMapping

        Raises:
            BrokerException: If mapping not found
        """
        logger.info(f"Updating account mapping ID: {mapping_id}")

        mapping = self.repository.get_by_id(mapping_id)
        if not mapping:
            raise BrokerException(
                "MessagesEnum.ACCOUNT_MAPPING_NOT_FOUND",
                f"Account mapping with ID {mapping_id} not found"
            )

        if code_gu1 is not None:
            mapping.code_gu1 = code_gu1
        if account_type is not None:
            mapping.account_type = account_type

        return self.repository.update(mapping)

    def delete_mapping(self, mapping_id: int) -> bool:
        """
        Soft delete an account mapping

        Args:
            mapping_id: Mapping ID

        Returns:
            True if deleted, False if not found
        """
        logger.info(f"Deleting account mapping ID: {mapping_id}")
        return self.repository.delete(mapping_id)

    def translate_to_external(self, internal_code: str) -> str:
        """
        Translate internal account code to external code
        If no mapping exists, returns the internal code

        Args:
            internal_code: Internal account code (GU3)

        Returns:
            External account code (GU1) or original code if no mapping
        """
        mapping = self.get_by_code_gu3(internal_code)
        if mapping:
            logger.debug(f"Translated account: {internal_code} -> {mapping.code_gu1}")
            return mapping.code_gu1
        logger.debug(f"No mapping found, using original code: {internal_code}")
        return internal_code

    def translate_to_internal(self, external_code: str) -> str:
        """
        Translate external account code to internal code
        If no mapping exists, returns the external code

        Args:
            external_code: External account code (GU1)

        Returns:
            Internal account code (GU3) or original code if no mapping
        """
        mapping = self.get_by_code_gu1(external_code)
        if mapping:
            logger.debug(f"Translated account: {external_code} -> {mapping.code_gu3}")
            return mapping.code_gu3
        logger.debug(f"No mapping found, using original code: {external_code}")
        return external_code