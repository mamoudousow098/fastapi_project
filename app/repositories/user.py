from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash


class UserRepository:
    """Repository pour gérer les utilisateurs"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get(self, user_id: int) -> User | None:
        """Récupère un utilisateur par ID"""
        return self.db.get(User, user_id)
    
    def get_by_email(self, email: str) -> User | None:
        """Récupère un utilisateur par email"""
        stmt = select(User).where(User.email == email)
        return self.db.scalar(stmt)
    
    def get_by_username(self, username: str) -> User | None:
        """Récupère un utilisateur par username"""
        stmt = select(User).where(User.username == username)
        return self.db.scalar(stmt)
    
    def get_multi(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Liste les utilisateurs"""
        stmt = select(User).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())
    
    def create(self, user_in: UserCreate) -> User:
        """Crée un utilisateur"""
        db_user = User(
            email=user_in.email,
            username=user_in.username,
            hashed_password=get_password_hash(user_in.password)
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update(self, user: User, user_in: UserUpdate) -> User:
        """Met à jour un utilisateur"""
        update_data = user_in.model_dump(exclude_unset=True)
        
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user_id: int) -> bool:
        """Supprime un utilisateur"""
        user = self.get(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False