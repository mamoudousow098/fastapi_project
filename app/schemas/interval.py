from pydantic import Field, field_validator
from app.core.base_model import CamelModel


class IntervalDTO(CamelModel):
    """Schema pour les intervalles de tarification"""
    
    minimum_amount: float = Field(
        ...,
        description="The minimum amount for the interval",
        ge=0
    )
    
    maximum_amount: float = Field(
        ...,
        description="The maximum amount for the interval",
        ge=0
    )
    
    percentage: float = Field(
        ...,
        description="The percentage for the interval",
        ge=0
    )
    
    fixe: float = Field(
        ...,
        description="The fixed part of the interval",
        ge=0
    )
    
    @field_validator('maximum_amount')
    @classmethod
    def validate_max_greater_than_min(cls, v: float, info) -> float:
        """Valider que maximum_amount >= minimum_amount"""
        if 'minimum_amount' in info.data and v < info.data['minimum_amount']:
            raise ValueError('maximum_amount must be greater than or equal to minimum_amount')
        return v


class IntervalCreate(IntervalDTO):
    """Schema pour la création d'un Interval"""
    pass


class IntervalUpdate(CamelModel):
    """Schema pour la mise à jour d'un Interval"""
    minimum_amount: float | None = None
    maximum_amount: float | None = None
    percentage: float | None = None
    fixe: float | None = None


class IntervalResponse(IntervalDTO):
    """Schema pour la réponse d'un Interval"""
    id: int
    
    class Config:
        from_attributes = True