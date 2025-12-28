"""
Movement Repository for database operations
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.movement import Movement


class MovementRepository:
    """Repository for Movement database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_gu_id(self, gu_id: str) -> Optional[Movement]:
        """Find movement by GUID"""
        return self.db.query(Movement).filter(
            Movement.gu_id == gu_id
        ).first()
    
    def find_by_id(self, movement_id: int) -> Optional[Movement]:
        """Find movement by ID"""
        return self.db.query(Movement).filter(
            Movement.id == movement_id
        ).first()
    
    def find_by_status(self, status_code: str) -> List[Movement]:
        """Find movements by status"""
        return self.db.query(Movement).filter(
            Movement.status_code == status_code
        ).all()
    
    def find_by_partner_dist_id(self, partner_dist_id: str) -> Optional[Movement]:
        """Find movement by partner distribution ID"""
        return self.db.query(Movement).filter(
            Movement.partner_dist_id == partner_dist_id
        ).first()
    
    def create(self, movement: Movement) -> Movement:
        """Create a new movement"""
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(movement)
        return movement
    
    def update(self, movement: Movement) -> Movement:
        """Update an existing movement"""
        self.db.commit()
        self.db.refresh(movement)
        return movement