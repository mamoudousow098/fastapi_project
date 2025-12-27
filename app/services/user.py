from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate, User as UserSchema
from app.core.security import verify_password


class UserService:
    """Service pour la logique métier utilisateur"""
    
    def __init__(self, db: Session):
        self.repository = UserRepository(db)
    
    def authenticate(self, username: str, password: str):
        """Authentifie un utilisateur"""
        user = self.repository.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_user(self, user_in: UserCreate) -> UserSchema:
        """Crée un nouvel utilisateur"""
        # Vérifier email
        if self.repository.get_by_email(user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Vérifier username
        if self.repository.get_by_username(user_in.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        user = self.repository.create(user_in)
        return UserSchema.model_validate(user)
    
    def get_user(self, user_id: int) -> UserSchema:
        """Récupère un utilisateur"""
        user = self.repository.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserSchema.model_validate(user)
    
    def list_users(self, skip: int = 0, limit: int = 100) -> list[UserSchema]:
        """Liste les utilisateurs"""
        users = self.repository.get_multi(skip=skip, limit=limit)
        return [UserSchema.model_validate(user) for user in users]