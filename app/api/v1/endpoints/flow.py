"""
Flow endpoints for FastAPI
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.flow import (
    FlowCreate,
    FlowResponse
)
from app.services.flow import FlowService
from app.models.enums import EntityState

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=list[FlowResponse])
async def get_all_flows(
    legal_entity: Optional[str] = Query(None, description="The legal entity code"),
    code: Optional[str] = Query(None, description="Flow code"),
    service_code: Optional[str] = Query(None, description="Service code"),
    status: Optional[str] = Query(None, description="Flow status"),
    page: int = Query(0, ge=0, description="Page number"),
    size: int = Query(100, ge=1, le=1000, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    Get a list of flows with optional filters
    """
    flow_service = FlowService(db)
    flows = flow_service.get_all_flows(
        legal_entity=legal_entity,
        code=code,
        service_code=service_code,
        status=status,
        page=page,
        size=size
    )
    
    if not flows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ENTITY_NOT_FOUND"
        )
    
    return flows


@router.get("/{code}", response_model=FlowResponse)
async def get_flow_by_code(
    code: str = Path(..., description="Flow code"),
    db: Session = Depends(get_db)
):
    """
    Get a flow by its code
    """
    flow_service = FlowService(db)
    flow = flow_service.get_flow_by_code(code)
    
    if not flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ENTITY_NOT_FOUND"
        )
    
    return flow


@router.post("", response_model=FlowResponse, status_code=status.HTTP_200_OK)
async def create_flow(
    flow_data: FlowCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new flow with impact rules and constraints
    
    Returns:
    - 200: SUCCESS
    - 409: ENTITY_ALREADY_EXISTS
    - 7059: There is already an active flow for this service code
    - 7027: Service not found for the given code
    - 7016: Product not found for the given code
    - 7020: Acquirer role not provided
    - 7021: Issuer role not provided
    - 7022: The impact must have the same number of intervals
    - 7023: The max amount should be greater than the min amount
    - 7024: The interval in the same line for all rules should have the same min and max value
    - 7025: The sum should be zero in each line to create the flow
    - 7000: Account type for the provided code not found
    - 7011: Account role not found for the given code
    - 7026: Impact rule type not found for the given code
    - 500: INTERNAL_SERVER_ERROR
    """
    logger.info("=" * 80)
    logger.info("Received flow creation request")
    logger.info(f"Flow data: {flow_data.model_dump_json(indent=2)}")
    logger.info("=" * 80)
    
    flow_service = FlowService(db)
    
    try:
        flow = flow_service.create_flow(flow_data)
        logger.info(f"Flow created successfully: {flow.code}")
        return FlowResponse.model_validate(flow)
    except ValueError as e:
        logger.error(f"ValueError during flow creation: {str(e)}", exc_info=True)
        error_message = str(e)
        
        # Map specific errors to status codes
        if "already exists" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="ENTITY_ALREADY_EXISTS"
            )
        elif "service" in error_message.lower() and "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SERVICE_NOT_FOUND"
            )
        elif "product" in error_message.lower() and "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PRODUCT_NOT_FOUND"
            )
        elif "acquirer" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ACQUIRER_ROLE_NOT_PROVIDED"
            )
        elif "issuer" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ISSUER_ROLE_NOT_PROVIDED"
            )
        elif "number of intervals" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="NUMBER_OF_INTERVAL_NOT_THE_SAME"
            )
        elif "maximum amount" in error_message.lower() and "greater" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MAX_AMOUNT_IS_NOT_GREATER"
            )
        elif "same min and max" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INTERVALS_DONT_HAVE_SAME_MIN_MAX"
            )
        elif "sum" in error_message.lower() and "zero" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SUM_IS_NOT_ZERO"
            )
        elif "account type" in error_message.lower() and "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ACCOUNT_TYPE_NOT_FOUND"
            )
        elif "account role" in error_message.lower() and "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ACCOUNT_ROLE_NOT_FOUND"
            )
        elif "impact rule type" in error_message.lower() and "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="IMPACT_RULE_TYPE_NOT_FOUND"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
    except Exception as e:
        logger.error(f"Unexpected error during flow creation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INTERNAL_SERVER_ERROR"
        )


@router.patch("/{code}", response_model=FlowResponse)
async def update_flow_status(
    code: str = Path(..., description="Flow code"),
    status_param: EntityState = Query(..., alias="status", description="New status"),
    db: Session = Depends(get_db)
):
    """
    Update flow status
    
    Returns:
    - 200: SUCCESS
    - 7017: Flow not found for the given code
    - 7018: Status not provided
    - 500: INTERNAL_SERVER_ERROR
    """
    if not status_param:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="STATUS_NOT_PROVIDED"
        )
    
    flow_service = FlowService(db)
    
    flow = flow_service.get_flow_by_code(code)
    if not flow:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="FLOW_NOT_FOUND"
        )
    
    try:
        updated_flow = flow_service.update_flow_status(code, status_param)
        return updated_flow
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INTERNAL_SERVER_ERROR"
        )


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flow(
    code: str = Path(..., description="Flow code"),
    db: Session = Depends(get_db)
):
    """
    Delete a flow (soft delete by setting deleted=True)
    """
    flow_service = FlowService(db)
    
    flow = flow_service.get_flow_by_code(code)
    if not flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FLOW_NOT_FOUND"
        )
    
    flow_service.delete_flow(code)
    return None