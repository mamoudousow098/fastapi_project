"""
Supporting service classes for parameter and account mapping
"""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.parameter import Parameter
from app.models.account_mapping import AccountMapping
from app.repositories.parameter import ParameterRepository
from app.services.movement import BrokerException

logger = logging.getLogger(__name__)


# ==================== ParameterService ====================
class ParameterService:
    """
    Service for managing system parameters
    Equivalent to Java ParameterService
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = ParameterRepository(db)

    def get_parameter_by_code(self, code: str, active_only: bool = True) -> Optional[Parameter]:
        """
        Get parameter by code

        Args:
            code: Parameter code to search for
            active_only: If True, only return active parameters

        Returns:
            Parameter if found, None otherwise
        """
        logger.info(f"Getting parameter by code: {code}")
        return self.repository.get_by_code(code, active_only)

    def get_parameter_by_id(self, prm_id: int) -> Optional[Parameter]:
        """Get parameter by ID"""
        return self.repository.get_by_id(prm_id)

    def get_all_active_parameters(self) -> List[Parameter]:
        """Get all active parameters"""
        return self.repository.get_all_active()

    def get_all_parameters(self) -> List[Parameter]:
        """Get all parameters (including inactive)"""
        return self.repository.get_all()

    def create_parameter(
            self,
            prm_code: str,
            prm_string_value: Optional[str] = None,
            prm_value: int = 1,
            prm_statut: int = 1
    ) -> Parameter:
        """
        Create a new parameter

        Args:
            prm_code: Parameter code
            prm_string_value: String value
            prm_value: Integer value (default: 1)
            prm_statut: Status (1=active, 0=inactive)

        Returns:
            Created Parameter
        """
        logger.info(f"Creating parameter: {prm_code}")

        # Check if parameter already exists
        existing = self.repository.get_by_code(prm_code, active_only=False)
        if existing:
            raise BrokerException(
                "MessagesEnum.PARAMETER_ALREADY_EXISTS",
                f"Parameter with code '{prm_code}' already exists"
            )

        parameter = Parameter(
            prm_code=prm_code,
            prm_string_value=prm_string_value,
            prm_value=prm_value,
            prm_statut=prm_statut
        )

        return self.repository.create(parameter)

    def update_parameter(
            self,
            prm_id: int,
            prm_string_value: Optional[str] = None,
            prm_value: Optional[int] = None,
            prm_statut: Optional[int] = None
    ) -> Parameter:
        """
        Update an existing parameter

        Args:
            prm_id: Parameter ID
            prm_string_value: New string value (optional)
            prm_value: New integer value (optional)
            prm_statut: New status (optional)

        Returns:
            Updated Parameter

        Raises:
            BrokerException: If parameter not found
        """
        logger.info(f"Updating parameter ID: {prm_id}")

        parameter = self.repository.get_by_id(prm_id)
        if not parameter:
            raise BrokerException(
                "MessagesEnum.PARAMETER_NOT_FOUND",
                f"Parameter with ID {prm_id} not found"
            )

        if prm_string_value is not None:
            parameter.prm_string_value = prm_string_value
        if prm_value is not None:
            parameter.prm_value = prm_value
        if prm_statut is not None:
            parameter.prm_statut = prm_statut

        return self.repository.update(parameter)

    def delete_parameter(self, prm_id: int) -> bool:
        """
        Soft delete a parameter (set prm_statut to 0)

        Args:
            prm_id: Parameter ID

        Returns:
            True if deleted, False if not found
        """
        logger.info(f"Deleting parameter ID: {prm_id}")
        return self.repository.delete(prm_id)

    def search_parameters(self, pattern: str, active_only: bool = True) -> List[Parameter]:
        """
        Search parameters by code pattern

        Args:
            pattern: Search pattern (uses SQL LIKE)
            active_only: If True, only return active parameters

        Returns:
            List of matching parameters
        """
        return self.repository.search_by_code_pattern(pattern, active_only)

    def get_url_parameter(self, service_code: str) -> Optional[Parameter]:
        """
        Get URL parameter for a service

        Args:
            service_code: Service code to get URL for

        Returns:
            Parameter containing the URL, or None
        """
        return self.get_parameter_by_code(service_code)

    def get_country_parameter(self, country_iso_code: str, suffix: str) -> Optional[Parameter]:
        """
        Get country-specific parameter

        Args:
            country_iso_code: Country ISO code (e.g., "SN", "CI")
            suffix: Parameter suffix (e.g., "_AGENT_LOGIN_GU1")

        Returns:
            Parameter if found, None otherwise
        """
        code = f"{country_iso_code}{suffix}"
        return self.get_parameter_by_code(code)


