"""
Flow schemas for request/response validation
"""
from datetime import datetime
from typing import List, Optional, Set
from pydantic import Field, field_validator,ConfigDict

from app.core.base_model import CamelModel
from app.models.enums import EntityState, CommissionBaseEnum


class IntervalSchema(CamelModel):
    """Interval schema for impact rules"""
    minimum_amount: float = Field(..., description="Minimum amount for the interval")
    maximum_amount: float = Field(..., description="Maximum amount for the interval")
    percentage: float = Field(0.0, description="Percentage to apply")
    fixe: float = Field(0.0, description="Fixed amount to apply")

    @field_validator('maximum_amount')
    @classmethod
    def validate_max_amount(cls, v, info):
        if 'minimum_amount' in info.data and v <= info.data['minimum_amount']:
            raise ValueError("Maximum amount must be greater than minimum amount")
        return v


class ImpactRuleSchema(CamelModel):
    """Impact rule schema"""
    code: str = Field(..., description="Rule code")
    label: str = Field(..., description="Rule label")
    account_role_code: str = Field(..., description="Account role code (ISSUER, ACQUIRER, etc.)")
    impact_rule_type_code: str = Field(..., description="Impact rule type code")
    account_types: List[str] = Field(default_factory=list, description="List of account type codes")
    intervals: List[IntervalSchema] = Field(..., min_length=1, description="List of intervals")


class ConstraintSchema(CamelModel):
    """Constraint schema"""
    code: str = Field(..., description="Constraint code")
    value: str = Field(..., description="Constraint value")
    movement_context: Optional[str] = Field(None, description="Movement context")


class ServiceProviderSchema(CamelModel):
    """Service provider schema"""
    provider: str = Field(..., description="Provider code")
    url: Optional[str] = Field(None, description="Provider URL")
    ranking: Optional[int] = Field(None, description="Provider ranking")
    gateway: Optional[str] = Field(None, description="Gateway identifier")


class FlowCreate(CamelModel):
    """Schema for creating a flow"""
    code: str = Field(..., min_length=1, description="Flow code")
    label: str = Field(..., min_length=1, description="Flow label")
    service_code: str = Field(..., description="Service code")
    application_date: Optional[int] = Field(None, description="Application date as timestamp (milliseconds)")
    date_format_application_date: Optional[datetime] = Field(None, description="Application date in datetime format")
    rules: List[ImpactRuleSchema] = Field(..., min_length=1, description="Impact rules")
    constraints: Optional[List[ConstraintSchema]] = Field(default_factory=list, description="Constraints")
    product_code: Optional[str] = Field(None, description="Product code")
    product_codes: Optional[Set[str]] = Field(None, description="Multiple product codes")
    account_number: Optional[str] = Field(None, description="Account number")
    client_category: Optional[str] = Field(None, description="Client category code")
    commission_base: Optional[CommissionBaseEnum] = Field(None, description="Commission base")
    provider: Optional[ServiceProviderSchema] = Field(None, description="Service provider")
    create_cancellation:  Optional[bool] = Field(None, description =" For create Another with the operation")

    @field_validator('rules')
    @classmethod
    def validate_rules(cls, v):
        if not v:
            raise ValueError("At least one impact rule is required")
        
        # Check for ACQUIRER and ISSUER roles
        roles = {rule.account_role_code for rule in v}
        if 'ACQUIRER' not in roles and 'ISSUER' not in roles:
            raise ValueError("At least one rule must have ACQUIRER or ISSUER role")
        
        # Check all rules have same number of intervals
        interval_counts = {len(rule.intervals) for rule in v}
        if len(interval_counts) > 1:
            raise ValueError("All rules must have the same number of intervals")
        
        return v


class FlowUpdate(CamelModel):
    """Schema for updating a flow"""
    status: EntityState = Field(..., description="New flow status")

# First, create Pydantic models for the nested objects
class ImpactRuleResponse(CamelModel):
    """Schema for impact rule response"""
    id: int
    code: str
    label: Optional[str] = None
    rule_account_role_id: Optional[int] = None
    impact_rule_type_id: Optional[int] = None
    flow_id: int
    status: EntityState
    creation_date: datetime
    updated_date: datetime
    deleted: bool
    
    model_config = ConfigDict(from_attributes=True)


class FlowConstraintResponse(CamelModel):
    """Schema for flow constraint response"""
    id: int
    code: str
    value: Optional[str] = None
    flow_id: int
    service_type_id: Optional[int] = None
    status: EntityState
    creation_date: datetime
    updated_date: datetime
    deleted: bool
    
    model_config = ConfigDict(from_attributes=True)


class ServiceProviderResponse(CamelModel):
    """Schema for service provider response"""
    id: int
    provider_id: int
    flow_id: int
    ranking: Optional[int] = None
    url: Optional[str] = None
    gateway: Optional[str] = None
    status: EntityState
    creation_date: datetime
    updated_date: datetime
    deleted: bool
    
    model_config = ConfigDict(from_attributes=True)


# Now update FlowResponse to use these models
class FlowResponse(CamelModel):
    """Schema for flow response"""
    id: int
    code: str
    label: str
    application_date: datetime
    service_code: str
    product_code: Optional[str] = None
    account_number: Optional[str] = None
    client_category: Optional[str] = None
    status: EntityState
    commission_base: Optional[CommissionBaseEnum] = None
    creation_date: datetime
    updated_date: datetime
    deleted: bool
    rules: List[ImpactRuleResponse] = []  # Changed from List[dict]
    constraints: List[FlowConstraintResponse] = []  # Changed from List[dict]
    provider: Optional[ServiceProviderResponse] = None  # Changed from dict
    version: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FlowList(CamelModel):
    """Schema for list of flows"""
    flows: List[FlowResponse]
    total: int
