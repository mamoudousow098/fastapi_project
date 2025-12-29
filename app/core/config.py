from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

import logging
import sys

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Configurer les loggers pour plus de détails
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger('app').setLevel(logging.DEBUG)


class Settings(BaseSettings):
    """Configuration de l'application"""
    
    # Application
    APP_NAME: str = "FastAPI REST API"
    VERSION: str = "1.0.0"
    ENV: str = "development"
    DEBUG: bool = True
    
    # Sécurité
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # PostgreSQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    
    # Pool de connexions
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    @property
    def DATABASE_URL(self) -> str:
        """URL de connexion PostgreSQL avec psycopg (version 3)"""
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """URL pour connexion asynchrone"""
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Keycloak OAuth2 Configuration
    KEYCLOAK_SERVER_URL: str = "https://intouchgu2-qlf.worldline-solutions.com/auth"
    KEYCLOAK_REALM: str = "sso-intouch-iacc"
    KEYCLOAK_CLIENT_ID: str = "agentapi"
    KEYCLOAK_CLIENT_SECRET: str = "GlDXf5TAk8XXt6lzn1M6UGaW1MwGIXkO"

    # Derived URLs
    @property
    def KEYCLOAK_ISSUER_URI(self) -> str:
        return f"{self.KEYCLOAK_SERVER_URL}/realms/{self.KEYCLOAK_REALM}"

    @property
    def KEYCLOAK_JWKS_URI(self) -> str:
        return f"{self.KEYCLOAK_ISSUER_URI}/protocol/openid-connect/certs"

    @property
    def KEYCLOAK_TOKEN_URI(self) -> str:
        return f"{self.KEYCLOAK_ISSUER_URI}/protocol/openid-connect/token"

    @property
    def KEYCLOAK_USERINFO_URI(self) -> str:
        return f"{self.KEYCLOAK_ISSUER_URI}/protocol/openid-connect/userinfo"

    # JWT Configuration
    JWT_ALGORITHM: str = "RS256"
    JWT_AUDIENCE: Optional[str] = None  # Set if your tokens have an audience claim

    # class Config:
    #     env_file = ".env"
    #     case_sensitive = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Retourne une instance unique de Settings (singleton)"""
    return Settings()


settings = get_settings()