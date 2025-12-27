from typing import Optional
from pydantic import Field
from app.core.base_model import CamelModel
from app.models.enums import ConstraintType, MovementContext


class ConstraintDTO(CamelModel):
    """Schema pour les contraintes"""
    
    code: ConstraintType = Field(
        ...,
        description="The constraint type it refers to"
    )
    
    value: Optional[str] = Field(
        None,
        description="The value of the constraint"
    )
    
    movement_context: Optional[MovementContext] = Field(
        None,
        description="The service flow i.e : INITIATION or VALIDATION"
    )


class ConstraintCreate(ConstraintDTO):
    """Schema pour la création d'une Constraint"""
    pass


class ConstraintUpdate(CamelModel):
    """Schema pour la mise à jour d'une Constraint"""
    code: Optional[ConstraintType] = None
    value: Optional[str] = None
    movement_context: Optional[MovementContext] = None


class ConstraintResponse(ConstraintDTO):
    """Schema pour la réponse d'une Constraint"""
    id: int
    
    class Config:
        from_attributes = True