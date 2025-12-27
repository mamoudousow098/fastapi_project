from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime


class UserBase(BaseModel):
    """Schéma de base utilisateur"""
    email: EmailStr = Field(..., description="Email de l'utilisateur")
    username: str = Field(..., min_length=3, max_length=50, description="Nom d'utilisateur")


class UserCreate(UserBase):
    """Schéma pour créer un utilisateur"""
    password: str = Field(..., min_length=8, description="Mot de passe (min 8 caractères)")


class UserUpdate(BaseModel):
    """Schéma pour mettre à jour un utilisateur"""
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=50)
    password: str | None = Field(None, min_length=8)
    is_active: bool | None = None


class UserInDB(UserBase):
    """Schéma utilisateur en base de données"""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class User(UserInDB):
    """Schéma utilisateur pour réponse API"""
    pass