"""
Movement API endpoints
"""
import logging
import traceback
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.financial.movement import (
    MovementExecutionRequest,
    MovementExecutionResponse
)
from app.services.movement_checker import MovementCheckerService
from app.services.movement_loader import MovementLoaderService
from app.core.security import get_user_from_token_verified

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/init",
    response_model=MovementExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Initiate a movement",
    description="Initiates a new financial movement transaction"
)
async def initiate_movement(
    request: MovementExecutionRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Initiate a new movement transaction.
    
    Args:
        request: Movement execution request containing transaction details
        authorization: Authorization header containing the bearer token
        db: Database session
        
    Returns:
        MovementExecutionResponse: Response containing movement execution details
        
    Raises:
        HTTPException: If the movement execution fails
    """
    logger.info("=" * 100)
    logger.info("RECEIVED NEW MOVEMENT INITIATION REQUEST")
    logger.info(f"Service Code: {request.service_code}")
    logger.info(f"Amount: {request.amount}")
    logger.info(f"Product Code: {request.product_code}")
    logger.info(f"Authorization present: {authorization is not None}")
    
    try:
        # Extract user from token
        logger.info("Extracting user from token...")
        kc_user = get_user_from_token_verified(authorization) if authorization else None
        logger.info(f"User extracted: {kc_user.get('username') if kc_user else 'No user'}")
        
        # Initialize the movement checker service
        logger.info("Initializing MovementCheckerService...")
        movement_checker_service = MovementCheckerService(db)
        
        # Create execution business object
        logger.info("Creating execution business object...")
        execution_bo = {
            "request": request,
            "kc_user": kc_user
        }
        
        # Launch the movement check
        logger.info("Launching movement check...")
        execution_result = movement_checker_service.launch_check(execution_bo)
        
        # Get the response
        logger.info("Getting response from execution result...")
        response = execution_result.get_response_from_request()
        
        logger.info(f"Response status: {response.response_details.code if response.response_details else 'N/A'}")
        logger.info(f"Response is error: {response.response_details.is_error if response.response_details else 'N/A'}")
        
        if response.response_details and response.response_details.is_error:
            logger.warning(f"Movement failed: {response.response_details.message}")
        else:
            logger.info("Movement initiated successfully!")
        
        logger.info("=" * 100)
        return response
        
    except Exception as e:
        logger.error("=" * 100)
        logger.error("CRITICAL ERROR IN ENDPOINT")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception message: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        logger.error("=" * 100)
        
        # Log the error and return appropriate HTTP exception
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )



@router.post(
    "/load",
    response_model=MovementExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="load a movement",
    description="load an existing movement transaction"
)
async def load_movement(
        request: MovementExecutionRequest,
        authorization: Optional[str] = Header(None),
        db: Session = Depends(get_db)
):
    """
    Initiate a new movement transaction.

    Args:
        request: Movement execution request containing transaction details
        authorization: Authorization header containing the bearer token
        db: Database session

    Returns:
        MovementExecutionResponse: Response containing movement execution details

    Raises:
        HTTPException: If the movement execution fails
    """
    logger.info("=" * 100)
    logger.info("RECEIVED NEW MOVEMENT INITIATION REQUEST")
    logger.info(f"Service Code: {request.service_code}")
    logger.info(f"Amount: {request.amount}")
    logger.info(f"Product Code: {request.product_code}")
    logger.info(f"Authorization present: {authorization is not None}")

    try:
        # Extract user from token
        logger.info("Extracting user from token...")
        kc_user = get_user_from_token_verified(authorization) if authorization else None
        logger.info(f"User extracted: {kc_user.get('username') if kc_user else 'No user'}")

        # Initialize the movement checker service
        logger.info("Initializing MovementLoadService...")
        movement_loader_service = MovementLoaderService (db)

        # Create execution business object
        logger.info("Creating execution business object...")
        execution_bo = {
            "request": request,
            "kc_user": kc_user
        }

        # Launch the movement check
        logger.info("Launching movement loader...")
        execution_result = movement_loader_service.load_movement(execution_bo)

        # Get the response
        logger.info("Getting response from execution result...")
        response = execution_result.get_response_from_request()

        logger.info(f"Response status: {response.response_details.code if response.response_details else 'N/A'}")
        logger.info(f"Response is error: {response.response_details.is_error if response.response_details else 'N/A'}")

        if response.response_details and response.response_details.is_error:
            logger.warning(f"Movement failed: {response.response_details.message}")
        else:
            logger.info("Movement loaded  successfully!")

        logger.info("=" * 100)
        return response

    except Exception as e:
        logger.error("=" * 100)
        logger.error("CRITICAL ERROR IN ENDPOINT")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception message: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        logger.error("=" * 100)

        # Log the error and return appropriate HTTP exception
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/init_and_load",
    response_model=MovementExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="init and load a movement",
    description="Initiates a new financial movement transaction"
)
async def init_and_load_movement(
        request: MovementExecutionRequest,
        authorization: Optional[str] = Header(None),
        db: Session = Depends(get_db)
):
    """
    Initiate a new movement transaction.

    Args:
        request: Movement execution request containing transaction details
        authorization: Authorization header containing the bearer token
        db: Database session

    Returns:
        MovementExecutionResponse: Response containing movement execution details

    Raises:
        HTTPException: If the movement execution fails
    """
    logger.info("=" * 100)
    logger.info("RECEIVED NEW MOVEMENT INITIATION REQUEST")
    logger.info(f"Service Code: {request.service_code}")
    logger.info(f"Amount: {request.amount}")
    logger.info(f"Product Code: {request.product_code}")
    logger.info(f"Authorization present: {authorization is not None}")

    try:
        # Extract user from token
        logger.info("Extracting user from token...")
        kc_user = get_user_from_token_verified(authorization) if authorization else None
        logger.info(f"User extracted: {kc_user.get('username') if kc_user else 'No user'}")

        # Initialize the movement checker service
        logger.info("Initializing init and load ...")
        logger.info("Creating execution business object...")
        execution_bo = {
            "request": request,
            "kc_user": kc_user
        }

        logger.info("Initializing MovementCheckerService...")
        movement_checker_service = MovementCheckerService(db)

        execution_result = movement_checker_service.launch_check(execution_bo)
        response = execution_result.get_response_from_request()
        if response.response_details and response.response_details.code == "SUCCESS" :
            logger.info("Initializing MovementLoaderService...")
            movement_loader_service = MovementLoaderService (db)
            execution_result = movement_loader_service.load_movement(execution_bo)
            # Get the response
            logger.info("Getting response from execution result...")
            response = execution_result.get_response_from_request()



        logger.info(f"Response status: {response.response_details.code if response.response_details else 'N/A'}")
        logger.info(f"Response is error: {response.response_details.is_error if response.response_details else 'N/A'}")

        if response.response_details and response.response_details.is_error:
            logger.warning(f"Movement failed: {response.response_details.message}")
        else:
            logger.info("Movement loaded  successfully!")

        logger.info("=" * 100)
        return response

    except Exception as e:
        logger.error("=" * 100)
        logger.error("CRITICAL ERROR IN ENDPOINT")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception message: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        logger.error("=" * 100)

        # Log the error and return appropriate HTTP exception
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )