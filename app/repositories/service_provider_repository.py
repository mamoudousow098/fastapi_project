"""
Repository classes for ServiceProvider and Provider
"""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload

from app.models.service_provider import ServiceProvider, Provider
from app.models.enums import Gateway

logger = logging.getLogger(__name__)


# ==================== ProviderRepository ====================
class ProviderRepository:
    """Repository for Provider entity"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, provider_id: int) -> Optional[Provider]:
        """Get provider by ID"""
        return self.db.query(Provider).filter(
            Provider.id == provider_id,
            Provider.deleted == False
        ).first()

    def get_by_code(self, code: str) -> Optional[Provider]:
        """
        Get provider by code

        Args:
            code: Provider code

        Returns:
            Provider if found, None otherwise
        """
        logger.debug(f"Getting provider by code: {code}")

        provider = self.db.query(Provider).filter(
            Provider.code == code,
            Provider.deleted == False
        ).first()

        if provider:
            logger.debug(f"Provider found: {code}")
        else:
            logger.debug(f"Provider not found: {code}")

        return provider

    def get_all(
            self,
            skip: int = 0,
            limit: int = 100
    ) -> List[Provider]:
        """Get all active providers"""
        return self.db.query(Provider).filter(
            Provider.deleted == False
        ).offset(skip).limit(limit).all()

    def create(self, provider: Provider) -> Provider:
        """Create a new provider"""
        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)
        logger.info(f"Created provider: {provider.code}")
        return provider

    def update(self, provider: Provider) -> Provider:
        """Update an existing provider"""
        self.db.commit()
        self.db.refresh(provider)
        logger.info(f"Updated provider: {provider.code}")
        return provider

    def delete(self, provider_id: int) -> bool:
        """Soft delete a provider"""
        provider = self.get_by_id(provider_id)
        if provider:
            provider.deleted = True
            self.db.commit()
            logger.info(f"Deleted provider: {provider.code}")
            return True
        return False

    def exists_by_code(self, code: str) -> bool:
        """Check if provider exists by code"""
        return self.db.query(Provider).filter(
            Provider.code == code,
            Provider.deleted == False
        ).first() is not None

    def get_with_service_providers(self, provider_id: int) -> Optional[Provider]:
        """Get provider with all its service providers (eager loading)"""
        return self.db.query(Provider).options(
            joinedload(Provider.service_providers)
        ).filter(
            Provider.id == provider_id,
            Provider.deleted == False
        ).first()


# ==================== ServiceProviderRepository ====================
class ServiceProviderRepository:
    """Repository for ServiceProvider entity"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, service_provider_id: int) -> Optional[ServiceProvider]:
        """Get service provider by ID with provider loaded"""
        return self.db.query(ServiceProvider).options(
            joinedload(ServiceProvider.provider)
        ).filter(
            ServiceProvider.id == service_provider_id,
            ServiceProvider.deleted == False
        ).first()

    def get_by_flow_id(self, flow_id: int) -> Optional[ServiceProvider]:
        """
        Get service provider by flow ID

        Args:
            flow_id: Flow ID

        Returns:
            ServiceProvider if found, None otherwise
        """
        logger.debug(f"Getting service provider by flow ID: {flow_id}")

        service_provider = self.db.query(ServiceProvider).options(
            joinedload(ServiceProvider.provider)
        ).filter(
            ServiceProvider.id_flow == flow_id,
            ServiceProvider.deleted == False
        ).first()

        if service_provider:
            logger.debug(f"ServiceProvider found for flow: {flow_id}")
        else:
            logger.debug(f"ServiceProvider not found for flow: {flow_id}")

        return service_provider

    def get_by_provider_code(self, provider_code: str) -> List[ServiceProvider]:
        """Get all service providers for a specific provider"""
        return self.db.query(ServiceProvider).join(
            Provider
        ).filter(
            Provider.code == provider_code,
            ServiceProvider.deleted == False,
            Provider.deleted == False
        ).all()

    def get_all(
            self,
            gateway: Optional[Gateway] = None,
            skip: int = 0,
            limit: int = 100
    ) -> List[ServiceProvider]:
        """
        Get all active service providers

        Args:
            gateway: Filter by gateway type (optional)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of ServiceProvider objects
        """
        query = self.db.query(ServiceProvider).options(
            joinedload(ServiceProvider.provider)
        ).filter(
            ServiceProvider.deleted == False
        )

        if gateway:
            query = query.filter(ServiceProvider.gateway == gateway)

        return query.offset(skip).limit(limit).all()

    def create(self, service_provider: ServiceProvider) -> ServiceProvider:
        """Create a new service provider"""
        self.db.add(service_provider)
        self.db.commit()
        self.db.refresh(service_provider)
        logger.info(f"Created service provider: {service_provider.id}")
        return service_provider

    def update(self, service_provider: ServiceProvider) -> ServiceProvider:
        """Update an existing service provider"""
        self.db.commit()
        self.db.refresh(service_provider)
        logger.info(f"Updated service provider: {service_provider.id}")
        return service_provider

    def delete(self, service_provider_id: int) -> bool:
        """Soft delete a service provider"""
        service_provider = self.get_by_id(service_provider_id)
        if service_provider:
            service_provider.deleted = True
            self.db.commit()
            logger.info(f"Deleted service provider: {service_provider.id}")
            return True
        return False

    def get_by_ranking(
            self,
            provider_code: str,
            min_ranking: Optional[int] = None,
            max_ranking: Optional[int] = None
    ) -> List[ServiceProvider]:
        """Get service providers by ranking range"""
        query = self.db.query(ServiceProvider).join(
            Provider
        ).filter(
            Provider.code == provider_code,
            ServiceProvider.deleted == False,
            Provider.deleted == False
        )

        if min_ranking is not None:
            query = query.filter(ServiceProvider.ranking >= min_ranking)
        if max_ranking is not None:
            query = query.filter(ServiceProvider.ranking <= max_ranking)

        return query.order_by(ServiceProvider.ranking).all()