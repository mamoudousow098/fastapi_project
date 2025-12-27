from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import get_db

router = APIRouter()


@router.get("/")
def health_check():
    """Health check simple"""
    return {"status": "ok", "message": "Service is healthy"}


@router.get("/db")
def health_check_db(db: Session = Depends(get_db)):
    """Health check avec test de connexion DB"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
