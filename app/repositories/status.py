# ============================================================================
# STATUS REPOSITORY
# ============================================================================
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.status import Status


class StatusRepository:
    """Repository for Status entity"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_code_and_deleted(self, code: str, deleted: bool = False) -> Optional[Status]:
        """
        Find status by code and deleted flag

        Args:
            code: Status code
            deleted: Deleted flag (default: False)

        Returns:
            Status entity or None
        """
        stmt = select(Status).where(
            Status.code == code,
            Status.deleted == deleted
        )
        result = self.db.execute(stmt).scalar_one_or_none()
        return result

    def find_by_code(self, code: str) -> Optional[Status]:
        """
        Find status by code (active only)

        Args:
            code: Status code

        Returns:
            Status entity or None
        """
        return self.find_by_code_and_deleted(code, deleted=False)

    def find_all(self, deleted: bool = False) -> List[Status]:
        """
        Find all statuses

        Args:
            deleted: Deleted flag (default: False)

        Returns:
            List of Status entities
        """
        stmt = select(Status).where(Status.deleted == deleted)
        result = self.db.execute(stmt).scalars().all()
        return list(result)

    def find_by_id(self, status_id: int) -> Optional[Status]:
        """
        Find status by ID

        Args:
            status_id: Status ID

        Returns:
            Status entity or None
        """
        return self.db.get(Status, status_id)

    def save(self, status: Status) -> Status:
        """
        Save or update status

        Args:
            status: Status entity

        Returns:
            Saved Status entity
        """
        self.db.add(status)
        self.db.flush()
        return status

    def delete(self, status: Status) -> None:
        """
        Soft delete status

        Args:
            status: Status entity
        """
        status.deleted = True
        status.updated_date = datetime.now()
        self.db.flush()