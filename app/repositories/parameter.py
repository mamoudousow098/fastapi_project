"""
Repository classes for database access
"""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.parameter import Parameter
from app.models.service_mapping import ServiceMapping
from app.models.account_mapping import AccountMapping

logger = logging.getLogger(__name__)


# ==================== ParameterRepository ====================
class ParameterRepository:
    """Repository for Parameter entity"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, code: str, active_only: bool = True) -> Optional[Parameter]:
        """
        Get parameter by code

        Args:
            code: Parameter code to search for
            active_only: If True, only return active parameters (prm_statut=1)

        Returns:
            Parameter if found, None otherwise
        """
        logger.debug(f"Getting parameter by code: {code} (active_only={active_only})")

        query = self.db.query(Parameter).filter(Parameter.prm_code == code)

        if active_only:
            query = query.filter(Parameter.prm_statut == 1)

        parameter = query.first()

        if parameter:
            logger.debug(f"Parameter found: {code} -> {parameter.prm_string_value}")
        else:
            logger.debug(f"Parameter not found: {code}")

        return parameter

    def get_by_id(self, prm_id: int) -> Optional[Parameter]:
        """Get parameter by ID"""
        return self.db.query(Parameter).filter(Parameter.prm_id == prm_id).first()

    def get_all_active(self) -> List[Parameter]:
        """Get all active parameters"""
        return self.db.query(Parameter).filter(Parameter.prm_statut == 1).all()

    def get_all(self) -> List[Parameter]:
        """Get all parameters"""
        return self.db.query(Parameter).all()

    def create(self, parameter: Parameter) -> Parameter:
        """Create a new parameter"""
        self.db.add(parameter)
        self.db.commit()
        self.db.refresh(parameter)
        return parameter

    def update(self, parameter: Parameter) -> Parameter:
        """Update an existing parameter"""
        self.db.commit()
        self.db.refresh(parameter)
        return parameter

    def delete(self, prm_id: int) -> bool:
        """Soft delete a parameter by setting prm_statut to 0"""
        parameter = self.get_by_id(prm_id)
        if parameter:
            parameter.prm_statut = 0
            self.db.commit()
            return True
        return False

    def search_by_code_pattern(self, pattern: str, active_only: bool = True) -> List[Parameter]:
        """
        Search parameters by code pattern

        Args:
            pattern: Pattern to search for (uses SQL LIKE)
            active_only: If True, only return active parameters

        Returns:
            List of matching parameters
        """
        query = self.db.query(Parameter).filter(Parameter.prm_code.like(f"%{pattern}%"))

        if active_only:
            query = query.filter(Parameter.prm_statut == 1)

        return query.all()
