"""
Flow repository for database operations
"""
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from sqlalchemy.sql.operators import or_

from app.models.flow import Flow
from app.models.enums import EntityState


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



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
    
    def find_by_service_code_and_status(
        self, 
        service_code: str, 
        status: EntityState, 
        deleted: bool = False
    ) -> Optional[Flow]:
        """Find flow by service code and status"""
        return self.db.query(Flow).filter(
            and_(
                Flow.service_code == service_code,
                Flow.status == status,
                Flow.deleted == deleted
            )
        ).first()
    
    def find_by_code_and_status(
        self, 
        code: str, 
        status: EntityState, 
        deleted: bool = False
    ) -> Optional[Flow]:
        """Find flow by code and status"""
        return self.db.query(Flow).filter(
            and_(
                Flow.code == code,
                Flow.status == status,
                Flow.deleted == deleted
            )
        ).first()
    
    # def find_by_service_and_filters(
    #     self,
    #     service_code: str,
    #     account_number: Optional[str],
    #     product_code: Optional[str],
    #     client_category: Optional[str],
    #     application_date_before: datetime,
    #     status: EntityState,
    #     deleted: bool = False
    # ) -> Optional[Flow]:
    #     """Find flow by service code and optional filters with priority"""
    #     query = self.db.query(Flow).filter(
    #         and_(
    #             Flow.service_code == service_code,
    #             Flow.application_date <= application_date_before,
    #             Flow.status == status,
    #             Flow.deleted == deleted
    #         )
    #     )
    #
    #     # Apply filters
    #     if account_number:
    #         query = query.filter(Flow.account_number == account_number)
    #     else:
    #         query = query.filter(Flow.account_number.is_(None))
    #
    #     if product_code:
    #         query = query.filter(Flow.product_code == product_code)
    #     else:
    #         query = query.filter(Flow.product_code.is_(None))
    #
    #     if client_category:
    #         query = query.filter(Flow.client_category == client_category)
    #     else:
    #         query = query.filter(Flow.client_category.is_(None))
    #
    #     return query.first()



    def find_by_service_and_filters(
            self,
            service_code: str,
            account_number: Optional[str] = None,
            product_code: Optional[str] = None,
            client_category: Optional[str] = None,
            is_cancellation: Optional[bool] = None,
            application_date_before: Optional[datetime] = None,
            status: Optional[EntityState] = None,
            deleted: bool = False
    ) -> Optional[Flow]:
        """
        Find flow by service code and optional filters

        Args:
            service_code: Required service code
            account_number: Optional account number filter
            product_code: Optional product code filter
            client_category: Optional client category filter
            is_cancellation: Optional cancellation flag filter
                - True: Find only cancellation flows
                - False: Find only normal flows
                - None: Find flows where is_cancellation is False or NULL
            application_date_before: Find flows with application_date <= this date
            status: Optional status filter
            deleted: Filter by deleted flag
        """
        logger.info(
            f"Repository search :: service={service_code}, "
            f"account={account_number}, product={product_code}, "
            f"category={client_category}, is_cancellation={is_cancellation}"
        )

        query = self.db.query(Flow).filter(
            Flow.service_code == service_code,
            Flow.deleted == deleted
        )

        # Filter by account_number (NULL or matching)
        if account_number is not None:
            query = query.filter(Flow.account_number == account_number)
        else:
            query = query.filter(Flow.account_number.is_(None))

        # Filter by product_code (NULL or matching)
        if product_code is not None:
            query = query.filter(Flow.product_code == product_code)
        else:
            query = query.filter(Flow.product_code.is_(None))

        # Filter by client_category (NULL or matching)
        if client_category is not None:
            query = query.filter(Flow.client_category == client_category)
        else:
            query = query.filter(Flow.client_category.is_(None))

        # Filter by is_cancellation
        if is_cancellation is True:
            # Explicitly looking for cancellation flows
            query = query.filter(Flow.is_cancellation == True)
        elif is_cancellation is False:
            # Explicitly looking for normal flows (False or NULL)
            query = query.filter(
                or_(
                    Flow.is_cancellation == False,
                    Flow.is_cancellation.is_(None)
                )
            )
        elif is_cancellation is None:
            # Default behavior: exclude cancellation flows
            query = query.filter(
                or_(
                    Flow.is_cancellation == False,
                    Flow.is_cancellation.is_(None)
                )
            )

        # Filter by application_date
        if application_date_before:
            query = query.filter(Flow.application_date <= application_date_before)

        # Filter by status
        if status:
            query = query.filter(Flow.status == status)

        # Order by application_date descending to get most recent
        query = query.order_by(Flow.application_date.desc())

        flow = query.first()

        if flow:
            logger.info(f"Flow found: {flow.code} (is_cancellation={flow.is_cancellation})")
        else:
            logger.info("No flow found matching criteria")

        return flow

