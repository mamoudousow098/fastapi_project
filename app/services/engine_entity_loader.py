"""
Engine Entity Loader Service - Business logic for loading entities
"""
import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Set, Dict
from passlib.context import CryptContext

from app.models import Status
from app.models.flow import Flow
from app.models.account import Account
from app.models.enums import EntityState, AccountCategory
from app.repositories.flow import FlowRepository
from app.repositories.account import AccountRepository
from app.repositories.status import StatusRepository
from app.repositories.repository import *
from app.services.movement import StatusBO

logger = logging.getLogger(__name__)

# Constants
AREA_CODE_PREFIX = "+"
AREA_CODE_PREFIX_WITH_2 = "+2"
PHONE_NUMBER_REGEX = r"^\+?\d{8,15}$"
MERCHANT_CODE_REGEX = r"^#?\w+$"
ALIAS_REGEX = r"^@\w+$"

# Password encoder (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class EngineEntityLoaderService:
    """Service for loading and retrieving entities"""

    STATUS_MAP: Dict[str, StatusBO] = {}

    def __init__(self, db: Session):
        self.db = db
        self.flow_repo = FlowRepository(db)
        self.account_repo = AccountRepository(db)
        self.service_repo = ServiceRepository(db)
        self.product_repo = ProductRepository(db)
        self.legal_entity_repo = LegalEntityRepository(db)
        self.country_repo = CountryRepository(db)
        self.status_repository = StatusRepository(db)
        
        # Cache for status (can be implemented with Redis in production)
        self._status_cache = {}
    
    def get_active_flow_by_service_code(self, service_code: str) -> Optional[Flow]:
        """Get active flow by service code"""
        return self.flow_repo.find_by_service_code_and_status(
            service_code=service_code,
            status=EntityState.ACTIVE,
            deleted=False
        )
    
    def get_flow_by_code(self, flow_code: str) -> Optional[Flow]:
        """Get flow by code"""
        return self.flow_repo.find_by_code_and_status(
            code=flow_code,
            status=EntityState.ACTIVE,
            deleted=False
        )
    
    # def get_active_flow_based_on_parameters(
    #     self,
    #     service_code: str,
    #     product_code: Optional[str] = None,
    #     account_number: Optional[str] = None,
    #     client_category: Optional[str] = None
    # ) -> Optional[Flow]:
    #     """
    #     Get active flow based on parameters with fallback logic
    #     Priority: account_number > client_category > product_code > default
    #     """
    #     logger.info(
    #         f"Searching for flow :: serviceCode: {service_code} "
    #         f"productCode: {product_code} accountNumber: {account_number}"
    #     )
    #
    #     try:
    #         current_date = datetime.now()
    #
    #         # 1. Try with account_number
    #         if account_number:
    #             flow = self.flow_repo.find_by_service_and_filters(
    #                 service_code=service_code,
    #                 account_number=account_number,
    #                 product_code=None,
    #                 client_category=None,
    #                 application_date_before=current_date,
    #                 status=EntityState.ACTIVE,
    #                 deleted=False
    #             )
    #             if flow:
    #                 return flow
    #
    #         # 2. Try with client_category
    #         if client_category:
    #             flow = self.flow_repo.find_by_service_and_filters(
    #                 service_code=service_code,
    #                 account_number=None,
    #                 product_code=None,
    #                 client_category=client_category,
    #                 application_date_before=current_date,
    #                 status=EntityState.ACTIVE,
    #                 deleted=False
    #             )
    #             if flow:
    #                 return flow
    #
    #         # 3. Try with product_code
    #         if product_code:
    #             flow = self.flow_repo.find_by_service_and_filters(
    #                 service_code=service_code,
    #                 account_number=None,
    #                 product_code=product_code,
    #                 client_category=None,
    #                 application_date_before=current_date,
    #                 status=EntityState.ACTIVE,
    #                 deleted=False
    #             )
    #             if flow:
    #                 return flow
    #
    #         # 4. Default flow (all NULL)
    #         flow = self.flow_repo.find_by_service_and_filters(
    #             service_code=service_code,
    #             account_number=None,
    #             product_code=None,
    #             client_category=None,
    #             application_date_before=current_date,
    #             status=EntityState.ACTIVE,
    #             deleted=False
    #         )
    #         return flow
    #
    #     except Exception as e:
    #         logger.error(f"Error retrieving active flow: {e}", exc_info=True)
    #         raise ValueError("Flow not found")
    #

    def get_active_flow_based_on_parameters(
            self,
            service_code: str,
            product_code: Optional[str] = None,
            account_number: Optional[str] = None,
            client_category: Optional[str] = None,
            is_cancellation: bool = False
        ) -> Optional[Flow]:
        """
            Get active flow based on parameters with fallback logic
            Priority: account_number > client_category > product_code > default

            Args:
                service_code: Service code to search for
                product_code: Optional product code
                account_number: Optional account number
                client_category: Optional client category
                is_cancellation: True for cancellation flows, False for normal flows
        """
        logger.info(
            f"Searching for flow :: serviceCode: {service_code} "
            f"productCode: {product_code} accountNumber: {account_number} "
            f"clientCategory: {client_category} isCancellation: {is_cancellation}"
        )

        try:
            current_date = datetime.now()

            # 1. Try with account_number
            if account_number:
                flow = self.flow_repo.find_by_service_and_filters(
                    service_code=service_code,
                    account_number=account_number,
                    product_code=None,
                    client_category=None,
                    is_cancellation=is_cancellation,
                    application_date_before=current_date,
                    status=EntityState.ACTIVE,
                    deleted=False
                )
                if flow:
                    logger.info(f"Flow found by account_number: {flow.code}")
                    return flow

            # 2. Try with client_category
            if client_category:
                flow = self.flow_repo.find_by_service_and_filters(
                    service_code=service_code,
                    account_number=None,
                    product_code=None,
                    client_category=client_category,
                    is_cancellation=is_cancellation,
                    application_date_before=current_date,
                    status=EntityState.ACTIVE,
                    deleted=False
                )
                if flow:
                    logger.info(f"Flow found by client_category: {flow.code}")
                    return flow

            # 3. Try with product_code
            if product_code:
                flow = self.flow_repo.find_by_service_and_filters(
                    service_code=service_code,
                    account_number=None,
                    product_code=product_code,
                    client_category=None,
                    is_cancellation=is_cancellation,
                    application_date_before=current_date,
                    status=EntityState.ACTIVE,
                    deleted=False
                )
                if flow:
                    logger.info(f"Flow found by product_code: {flow.code}")
                    return flow

            # 4. Default flow (all NULL except service_code and is_cancellation)
            flow = self.flow_repo.find_by_service_and_filters(
                service_code=service_code,
                account_number=None,
                product_code=None,
                client_category=None,
                is_cancellation=is_cancellation,
                application_date_before=current_date,
                status=EntityState.ACTIVE,
                deleted=False
            )

            if flow:
                logger.info(f"Default flow found: {flow.code}")
            else:
                logger.warning(
                    f"No flow found for service={service_code}, "
                    f"is_cancellation={is_cancellation}"
                )

            return flow

        except Exception as e:
            logger.error(f"Error retrieving active flow: {e}", exc_info=True)
            raise ValueError("Flow not found")

    def get_account_by_account_number_or_phone_or_merchant(
        self,
        account_identifier: str,
        service: Service
    ) -> Optional[Account]:
        """
        Get account by account number, phone number, or merchant code
        """
        try:
            if not account_identifier:
                return None
            
            # 1. Check if it's a phone number
            if re.match(PHONE_NUMBER_REGEX, account_identifier):
                phone = account_identifier
                
                # Add area code if needed
                if not phone.startswith(AREA_CODE_PREFIX_WITH_2):
                    if (service.legal_entity and 
                        service.legal_entity.country and 
                        service.legal_entity.country.area_code):
                        phone = f"{AREA_CODE_PREFIX}{service.legal_entity.country.area_code}{phone}"
                
                logger.info(f"Searching for account with phone: {phone}")
                accounts = self.account_repo.find_by_phone_number(phone, deleted=False)
                
                if not accounts:
                    return None
                
                if len(accounts) > 1:
                    # Prefer CUSTOMER accounts
                    customer_account = next(
                        (acc for acc in accounts if acc.category == AccountCategory.CUSTOMER),
                        None
                    )
                    return customer_account if customer_account else accounts[0]
                
                return accounts[0]
            
            # 2. Check if it's a merchant code (must start with #)
            elif account_identifier.startswith("#") and re.match(MERCHANT_CODE_REGEX, account_identifier):
                merchant_code = account_identifier.replace("#", "")
                logger.info(f"Searching for account with merchant code: {merchant_code}")
                return self.account_repo.find_by_merchant_code(merchant_code, deleted=False)
            
            # 3. Default: search by account number
            else:
                logger.info(f"Searching for account with account number: {account_identifier}")
                return self.account_repo.find_by_account_number(account_identifier, deleted=False)
            
        except Exception as e:
            logger.error(f"Error retrieving account {account_identifier}: {e}", exc_info=True)
            raise ValueError("Account not found")

    def get_account_by_identifier_or_alias(
        self,
        account_identifier: str,
        service: Service
    ) -> Optional[Account]:
        """
        Get account by account number, phone number, merchant code, or alias
        """
        try:
            if not account_identifier:
                return None
            
            # 1. Check if it's a phone number
            if re.match(PHONE_NUMBER_REGEX, account_identifier):
                phone = account_identifier
                
                if not phone.startswith(AREA_CODE_PREFIX_WITH_2):
                    if (service.legal_entity and 
                        service.legal_entity.country and 
                        service.legal_entity.country.area_code):
                        phone = f"{AREA_CODE_PREFIX}{service.legal_entity.country.area_code}{phone}"
                
                logger.info(f"Searching for account with phone: {phone}")
                accounts = self.account_repo.find_by_phone_number(phone, deleted=False)
                
                if not accounts:
                    return None
                
                if len(accounts) > 1:
                    customer_account = next(
                        (acc for acc in accounts if acc.category == AccountCategory.CUSTOMER),
                        None
                    )
                    return customer_account if customer_account else accounts[0]
                
                return accounts[0]
            
            # 2. Check if it's a merchant code
            if re.match(MERCHANT_CODE_REGEX, account_identifier):
                merchant_code = account_identifier.replace("#", "")
                logger.info(f"Searching for account with merchant code: {merchant_code}")
                return self.account_repo.find_by_merchant_code(merchant_code, deleted=False)
            
            # 3. Check if it's an alias
            if re.match(ALIAS_REGEX, account_identifier):
                logger.info(f"Alias condition met: {account_identifier}")
                alias_value = account_identifier.replace("@", "")
                
                # Get alias and resolve to real account number
                alias = self._get_alias(alias_value)
                if alias:
                    real_account_number = alias.other
                    logger.info(f"Searching for account with resolved alias: {real_account_number}")
                    return self.account_repo.find_by_account_number(real_account_number, deleted=False)
            
            # 4. Default: search by account number
            logger.info(f"Searching for account with account number: {account_identifier}")
            return self.account_repo.find_by_account_number(account_identifier, deleted=False)
            
        except Exception as e:
            logger.error(f"Error retrieving account {account_identifier}: {e}", exc_info=True)
            raise ValueError("Account not found")
    
    def _get_alias(self, alias_value: str):
        """Get alias by value (implementation depends on your Alias model)"""
        # TODO: Implement alias repository
        logger.info(f"Searching for alias: {alias_value}")
        # from app.repositories.alias import AliasRepository
        # alias_repo = AliasRepository(self.db)
        # return alias_repo.find_by_alias_or_shid(alias_value)
        return None
    
    def find_service(self, service_code: str) -> Optional[Service]:
        """Find service by code"""
        return self.service_repo.find_by_code(service_code, deleted=False)
    
    def find_product(self, product_code: str) -> Optional[Product]:
        """Find product by code"""
        return self.product_repo.find_by_code(product_code, deleted=False)
    
    def get_legal_entity_by_code(self, legal_entity_code: str) -> Optional[LegalEntity]:
        """Get legal entity by code"""
        return self.legal_entity_repo.find_by_code(legal_entity_code, deleted=False)
    
    def get_country_by_iso_code(self, country_iso_code: str) -> Optional[Country]:
        """Get country by ISO code"""
        return self.country_repo.find_by_iso_code(country_iso_code, deleted=False)
    
    def find_provider_accounts(self, provider_id: int, provider_account_types: list) -> Set[Account]:
        """Find provider accounts by provider ID and account types"""
        logger.info(f"Searching for provider accounts ID: {provider_id}")
        return self.account_repo.find_by_provider_and_types(provider_id, provider_account_types)

    def get_status_by_code(self, status_code: str) -> Optional[StatusBO]:
        """
        Get status by code with caching

        Args:
            status_code: Status code to find

        Returns:
            StatusBO or None if not found
        """
        # Check cache first
        if status_code in self.STATUS_MAP:
            logger.debug(f"Status found in cache: {status_code}")
            return self.STATUS_MAP[status_code]

        # Query database
        status = self.status_repository.find_by_code_and_deleted(status_code, deleted=False)

        if status:
            # Create StatusBO and cache it
            status_bo = StatusBO(status)
            self.STATUS_MAP[status_code] = status_bo
            logger.info(f"Status loaded and cached: {status_code}")
            return status_bo

        logger.warning(f"Status not found: {status_code}")
        return None

    def get_status_by_code_or_create(self, status_code: str, label: str = None, message: str = None) -> StatusBO:
        """
        Get status by code, create if not exists

        Args:
            status_code: Status code
            label: Status label (optional)
            message: Status message (optional)

        Returns:
            StatusBO
        """
        status_bo = self.get_status_by_code(status_code)

        if not status_bo:
            # Create new status
            new_status = Status(
                code=status_code,
                label=label or status_code,
                message=message or status_code
            )
            self.status_repository.save(new_status)
            self.db.commit()

            # Cache and return
            status_bo = StatusBO(new_status)
            self.STATUS_MAP[status_code] = status_bo
            logger.info(f"New status created and cached: {status_code}")

        return status_bo

    def clear_status_cache(self) -> None:
        """Clear the status cache"""
        self.STATUS_MAP.clear()
        logger.info("Status cache cleared")

    def preload_statuses(self) -> None:
        """Preload all active statuses into cache"""
        logger.info("Preloading statuses into cache...")

        statuses = self.status_repository.find_all(deleted=False)
        for status in statuses:
            status_bo = StatusBO(status)
            self.STATUS_MAP[status.code] = status_bo

        logger.info(f"Preloaded {len(statuses)} statuses into cache")
