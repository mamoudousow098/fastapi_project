from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool
from app.core.config import settings

# Créer le moteur PostgreSQL avec pool de connexions
engine = create_engine(
    settings.DATABASE_URL,
    
    # Vérifier les connexions avant utilisation
    pool_pre_ping=True,
    
    # Configuration du pool
    pool_size=settings.DB_POOL_SIZE,           # Connexions persistantes
    max_overflow=settings.DB_MAX_OVERFLOW,     # Connexions supplémentaires
    pool_timeout=settings.DB_POOL_TIMEOUT,     # Timeout en secondes
    pool_recycle=settings.DB_POOL_RECYCLE,     # Recycler après X secondes
    
    # Logger les requêtes SQL en mode debug
    echo=settings.DEBUG,
    
    # Options PostgreSQL spécifiques
    connect_args={
        "options": "-c timezone=utc"  # Forcer UTC
    }
)


# Event listener pour optimiser PostgreSQL
@event.listens_for(Pool, "connect")
def set_postgres_pragma(dbapi_connection, connection_record):
    """Configure la connexion PostgreSQL"""
    cursor = dbapi_connection.cursor()
    # Optimisations PostgreSQL
    cursor.execute("SET statement_timeout = '60s'")  # Timeout requêtes
    cursor.execute("SET lock_timeout = '30s'")       # Timeout locks
    cursor.close()


# Factory de sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Session:
    """
    Dépendance FastAPI pour obtenir une session DB
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_context():
    """
    Context manager pour utilisation hors FastAPI
    Usage:
        with get_db_context() as db:
            # utiliser db
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
