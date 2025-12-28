"""
Additional repositories for Service, Product, LegalEntity, and Country
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.service import Service
from app.models.product import Product
from app.models.legal_entity import LegalEntity
from app.models.country import Country


class ServiceRepository:
    """Repository for Service database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_code(self, code: str, deleted: bool = False) -> Optional[Service]:
        """Find service by code"""
        return self.db.query(Service).filter(
            and_(
                Service.code == code,
                Service.deleted == deleted
            )
        ).first()


class ProductRepository:
    """Repository for Product database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_code(self, code: str, deleted: bool = False) -> Optional[Product]:
        """Find product by code"""
        return self.db.query(Product).filter(
            and_(
                Product.code == code,
                Product.deleted == deleted
            )
        ).first()


class LegalEntityRepository:
    """Repository for LegalEntity database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_code(self, code: str, deleted: bool = False) -> Optional[LegalEntity]:
        """Find legal entity by code"""
        return self.db.query(LegalEntity).filter(
            and_(
                LegalEntity.code == code,
                LegalEntity.deleted == deleted
            )
        ).first()


class CountryRepository:
    """Repository for Country database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_iso_code(self, iso_code: str, deleted: bool = False) -> Optional[Country]:
        """Find country by ISO code"""
        return self.db.query(Country).filter(
            and_(
                Country.iso_code == iso_code,
                Country.deleted == deleted
            )
        ).first()