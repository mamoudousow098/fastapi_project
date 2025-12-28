"""
Movement Service - Equivalent to MovementServiceBean
"""
import logging
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.movement import Movement
from app.models.history_mvt_status import HistoryMvtStatus
from app.models.enums import StatusEnum
from app.repositories.movement import MovementRepository

logger = logging.getLogger(__name__)


class BrokerException(Exception):
    """Custom broker exception"""
    def __init__(self, message: str, code: str = "BROKER_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class NoStatusChangingBrokerException(BrokerException):
    """Exception that doesn't change status"""
    pass


class StatusBO:
    """Status Business Object"""
    def __init__(self, code: str, message: str = None):
        self.code = code
        self.message = message or code


class MovementService:
    """Service for movement operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = MovementRepository(db)
    
    def create(self, movement: Movement) -> Movement:
        """
        Create a new movement
        """
        try:
            logger.info(f"Creating movement: {movement.gu_id}")
            self.db.add(movement)
            self.db.commit()
            self.db.refresh(movement)
            logger.info(f"Movement created successfully with ID: {movement.id}")
            return movement
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating movement: {e}")
            if "ConstraintViolationException" in str(e) or "duplicate" in str(e).lower():
                raise BrokerException("Duplicated movement", "DUPLICATED_MOVEMENT")
            raise BrokerException("Cannot save movement", "CANNOT_SAVE_MOVEMENT")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating movement: {e}", exc_info=True)
            raise BrokerException("Cannot save movement", "CANNOT_SAVE_MOVEMENT")
    
    def find_by_guid(self, guid: str) -> Optional[Movement]:
        """
        Find movement by GUID
        """
        try:
            logger.info(f"Finding movement by GUID: {guid}")
            movement = self.repository.find_by_gu_id(guid)
            if movement:
                logger.info(f"Movement found: ID {movement.id}")
            else:
                logger.info(f"Movement not found for GUID: {guid}")
            return movement
        except Exception as e:
            logger.error(f"Error finding movement by GUID: {e}", exc_info=True)
            return None
    
    def update_status(
        self,
        movement: Movement,
        status: StatusBO,
        author: str,
        message: str
    ) -> Movement:
        """
        Update movement status and create history entry
        """
        logger.info(f"Updating movement status: {movement.gu_id} -> {status.code}")
        
        if not status:
            raise NoStatusChangingBrokerException("Status not found", "STATUS_NOT_FOUND")
        
        if not movement:
            return None
        
        try:
            # Create history entry
            history = HistoryMvtStatus(
                status=status.code,
                message=status.message or message,
                author=author,
                gu_id=movement.gu_id
            )
            self.db.add(history)
            
            # Update movement based on status
            if status.code == StatusEnum.PART_FAILED.value:
                movement.end_date = datetime.now()
                # TODO: Delete from movement_temp
            elif status.code in [StatusEnum.PART_SUCCESSFUL.value, StatusEnum.BK_SUCCESSFUL.value]:
                movement.end_date = datetime.now()
            elif status.code == StatusEnum.CANCELLED.value:
                movement.cancellation_date = datetime.now()
            
            # Update status and message
            movement.status_code = status.code
            movement.message = message
            
            # Commit changes
            self.db.commit()
            self.db.refresh(movement)
            
            # TODO: Send to pub/sub topic for logging
            logger.info(f"Movement status updated successfully: {status.code}")
            
            return movement
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating movement status: {e}", exc_info=True)
            return None
    
    def update_status_movement(
        self,
        movement_id: int,
        status: StatusBO,
        author: str,
        message: str,
        impact_date: Optional[datetime] = None
    ) -> None:
        """
        Update movement status using direct SQL (for performance)
        """
        logger.info(f"Updating movement status (SQL): ID {movement_id} -> {status.code}")
        
        if not status:
            raise NoStatusChangingBrokerException("Status not found", "STATUS_NOT_FOUND")
        
        try:
            # Create history entry
            history = HistoryMvtStatus(
                status=status.code,
                message=status.message or message,
                author=author,
                gu_id=f"ID_{movement_id}"  # Using ID as fallback
            )
            self.db.add(history)
            
            # Update based on status
            if status.code == StatusEnum.SUCCESSFUL.value:
                sql = text("""
                    UPDATE movement 
                    SET status_code = :status, 
                        message = :message,
                        impact_date = CASE 
                            WHEN :date IS NULL THEN NOW() 
                            ELSE COALESCE(impact_date, :date)
                        END
                    WHERE id = :id
                """)
                
                self.db.execute(sql, {
                    "status": status.code,
                    "message": message,
                    "id": movement_id,
                    "date": impact_date
                })
                
            elif status.code == StatusEnum.CANCELLED.value:
                sql = text("""
                    UPDATE movement 
                    SET status_code = :status,
                        cancellation_date = NOW()
                    WHERE id = :id
                """)
                
                self.db.execute(sql, {
                    "status": status.code,
                    "id": movement_id
                })
            
            self.db.commit()
            logger.info(f"Movement status updated successfully via SQL")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating movement status: {e}", exc_info=True)
    
    def get_total_amount(self, account_number: str) -> float:
        """
        Get total pending amount for an account
        """
        logger.info(f"Getting total pending amount for account: {account_number}")
        
        try:
            sql = text("""
                SELECT SUM(m.amount) AS sum_amount
                FROM movement m
                WHERE m.status_code IN (
                    'BK_INITIATED', 'BK_LOADED', 
                    'PART_INITIATED', 'PART_LOADED'
                )
                AND m.issuer_account = :account_number
            """)
            
            result = self.db.execute(sql, {"account_number": account_number}).scalar()
            total = float(result) if result else 0.0
            
            logger.info(f"Total pending amount: {total}")
            return total
            
        except Exception as e:
            logger.error(f"Error getting total amount: {e}", exc_info=True)
            return 0.0