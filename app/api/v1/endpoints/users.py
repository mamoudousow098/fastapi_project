from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.user import UserService
from app.schemas.user import User, UserCreate
from app.core.dependencies import get_current_active_user
from app.models.user import User as UserModel

router = APIRouter()


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Créer un nouvel utilisateur (public)"""
    service = UserService(db)
    return service.create_user(user_in)


@router.get("/me", response_model=User)
def read_current_user(current_user: UserModel = Depends(get_current_active_user)):
    """Récupérer l'utilisateur connecté"""
    return current_user


@router.get("/{user_id}", response_model=User)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Récupérer un utilisateur par ID (protégé)"""
    service = UserService(db)
    return service.get_user(user_id)


@router.get("/", response_model=list[User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Lister les utilisateurs (protégé)"""
    service = UserService(db)
    return service.list_users(skip=skip, limit=limit)
