from fastapi import APIRouter
from app.api.v1.endpoints import health, users, auth, flow, movement

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(flow.router, prefix="/flows", tags=["flows"]) 

# Include movement endpoints
api_router.include_router(
    movement.router, 
    prefix="/movement", 
    tags=["movement"]
)