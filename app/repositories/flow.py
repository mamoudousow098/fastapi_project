"""
Flow repository for database operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.models.flow import Flow
from app.models.enums import EntityState


class FlowRepository:
    """Repository for Flow database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(
        self,
        legal_entity: Optional[str] = None,
        code: Optional[str] = None,
        service_code: Optional[str] = None,
        status: Optional[EntityState] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Flow]:
        """Get all flows with optional filters"""
        query = self.db.query(Flow).options(
            joinedload(Flow.rules),
            joinedload(Flow.constraints),
            joinedload(Flow.provider)
        )
        
        filters = []
        
        if legal_entity:
            filters.append(Flow.legal_entity_code == legal_entity)
        
        if code:
            filters.append(Flow.code.ilike(f"%{code}%"))
        
        if service_code:
            filters.append(Flow.service_code == service_code)
        
        if status:
            filters.append(Flow.status == status)
        
        if filters:
            query = query.filter(and_(*filters))
        
        return query.offset(skip).limit(limit).all()
    
    def get_by_code(self, code: str) -> Optional[Flow]:
        """Get flow by code"""
        return self.db.query(Flow).options(
            joinedload(Flow.rules),
            joinedload(Flow.constraints),
            joinedload(Flow.provider)
        ).filter(Flow.code == code).first()
    
    def get_by_id(self, flow_id: int) -> Optional[Flow]:
        """Get flow by ID"""
        return self.db.query(Flow).options(
            joinedload(Flow.rules),
            joinedload(Flow.constraints),
            joinedload(Flow.provider)
        ).filter(Flow.id == flow_id).first()
    
    def create(self, flow: Flow) -> Flow:
        """Create a new flow"""
        self.db.add(flow)
        self.db.commit()
        self.db.refresh(flow)
        return flow
    
    def update(self, flow: Flow) -> Flow:
        """Update an existing flow"""
        self.db.commit()
        self.db.refresh(flow)
        return flow
    
    def delete(self, flow: Flow) -> None:
        """Delete a flow"""
        self.db.delete(flow)
        self.db.commit()
    
    def exists_by_code(self, code: str) -> bool:
        """Check if flow exists by code"""
        return self.db.query(Flow).filter(Flow.code == code).first() is not None