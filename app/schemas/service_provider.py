from typing import Optional
from pydantic import Field, HttpUrl
from app.core.base_model import CamelModel
from app.models.enums import Gateway


class ServiceProviderExchange(CamelModel):
    """Schema pour l'échange de Service Provider"""
    
    provider: str = Field(
        ...,
        min_length=1,
        description="The account number of the provider account"
    )
    
    ranking: int = Field(
        ...,
        description="Provider ranking",
        ge=0
    )
    
    url: str = Field(
        ...,
        min_length=1,
        description="Provider URL"
    )
    
    gateway: Optional[Gateway] = Field(
        None,
        description="Gateway type: USSD, APIDIST, or CONNECTOR"
    )


class ServiceProviderCreate(ServiceProviderExchange):
    """Schema pour la création d'un Service Provider"""
    pass


class ServiceProviderUpdate(CamelModel):
    """Schema pour la mise à jour d'un Service Provider"""
    provider: Optional[str] = None
    ranking: Optional[int] = None
    url: Optional[str] = None
    gateway: Optional[Gateway] = None


class ServiceProviderResponse(ServiceProviderExchange):
    """Schema pour la réponse d'un Service Provider"""
    id: int
    
    class Config:
        from_attributes = True