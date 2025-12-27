from typing import Optional
from pydantic import Field
from app.core.base_model import CamelModel
from app.schemas.interval import IntervalDTO


class ImpactRuleExchange(CamelModel):
    """Schema pour l'échange d'Impact Rule"""
    
    code: str = Field(
        ..., 
        min_length=1,
        description="The Impact rule code"
    )
    
    label: Optional[str] = Field(
        None,
        description="The label for the impact rule"
    )
    
    intervals: Optional[list[IntervalDTO]] = Field(
        None,
        description="The intervals list related to the impact rule"
    )
    
    account_role_code: str = Field(
        ...,
        min_length=1,
        description="The Code of the account role related to impact rule type"
    )
    
    account_types: Optional[set[str]] = Field(
        None,
        description="Set of account types"
    )
    
    impact_rule_type_code: str = Field(
        ...,
        min_length=1,
        description="The code of the impact rule type related to the impact rule"
    )


class ImpactRuleCreate(ImpactRuleExchange):
    """Schema pour la création d'un Impact Rule"""
    pass


class ImpactRuleUpdate(CamelModel):
    """Schema pour la mise à jour d'un Impact Rule"""
    code: Optional[str] = None
    label: Optional[str] = None
    intervals: Optional[list[IntervalDTO]] = None
    account_role_code: Optional[str] = None
    account_types: Optional[set[str]] = None
    impact_rule_type_code: Optional[str] = None


class ImpactRuleResponse(ImpactRuleExchange):
    """Schema pour la réponse d'un Impact Rule"""
    id: int
    
    class Config:
        from_attributes = True