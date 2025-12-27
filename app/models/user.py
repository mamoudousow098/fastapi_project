# app/models/user.py
from app.models.base import Base, AbstractAttributEntity  # ← Changez ici
from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

class User(AbstractAttributEntity):  # Ou Base selon votre structure
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)