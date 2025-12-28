"""
Account repository for database operations
"""
from typing import List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.account import Account


class AccountRepository:
    """Repository for Account database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_account_number(self, account_number: str, deleted: bool = False) -> Optional[Account]:
        """Find account by account number"""
        return self.db.query(Account).filter(
            and_(
                Account.account_number == account_number,
                Account.deleted == deleted
            )
        ).first()
    
    def find_by_phone_number(self, phone_number: str, deleted: bool = False) -> List[Account]:
        """Find accounts by phone number"""
        return self.db.query(Account).filter(
            and_(
                Account.phone_number == phone_number,
                Account.deleted == deleted
            )
        ).all()
    
    def find_by_merchant_code(self, merchant_code: str, deleted: bool = False) -> Optional[Account]:
        """Find account by merchant code"""
        return self.db.query(Account).filter(
            and_(
                Account.merchant_code == merchant_code,
                Account.deleted == deleted
            )
        ).first()
    
    def find_by_provider_and_types(self, provider_id: int, account_types: list) -> Set[Account]:
        """Find accounts by provider ID and account types"""
        # This requires a join with account_account_type table
        from app.models.account_dependency import AccountType
        
        accounts = self.db.query(Account).join(
            Account.account_types
        ).filter(
            and_(
                Account.provider_id == provider_id,
                AccountType.code.in_(account_types),
                Account.deleted == False
            )
        ).all()
        
        return set(accounts)