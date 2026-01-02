"""
Exchange schemas for external partner communication
Equivalent to Java DTO classes
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional
from datetime import datetime


# ==================== ExchangeAbstract Base Schema ====================
class ExchangeAbstract(BaseModel):
    """
    Base class for all exchange DTOs
    Equivalent to Java ExchangeAbstract class
    """

    model_config = ConfigDict(populate_by_name=True)

    token: Optional[str] = None
    date: Optional[int] = None
    merchant_code: Optional[str] = Field(None, alias="merchantCode")
    adresse_mac: Optional[str] = Field(None, alias="adresseMAC")
    code_pda: Optional[str] = Field(None, alias="codePDA")
    login_agent: Optional[str] = Field(None, alias="loginAgent")
    sale_point_code: Optional[str] = Field(None, alias="salePointCode")
    error_code: Optional[str] = Field(None, alias="errorCode")
    error_message: Optional[str] = Field(None, alias="errorMessage")
    code_proxy: Optional[str] = Field(None, alias="codeProxy")
    token_pda: Optional[str] = Field(None, alias="tokenPda")

    # Transient fields (not serialized by default)
    response_body: Optional[str] = Field(None, exclude=True, alias="responseBody")
    response_code: Optional[int] = Field(None, exclude=True, alias="responseCode")

    def get_error_code_and_message_to_string(self) -> str:
        """Get formatted error code and message"""
        return f"CODE [ {self.error_code} ] And MESSAGE [ {self.error_message} ]"


# ==================== ServiceExchange Schema ====================
class ServiceExchange(BaseModel):
    """
    Service exchange DTO for external partner calls
    Equivalent to Java ServiceExchange class
    """

    model_config = ConfigDict(populate_by_name=True)

    service_code: Optional[str] = Field(None, alias="serviceCode")
    srv_paiement_mode: Optional[str] = Field(None, alias="srvPaiementMode")
    service_remise: Optional[float] = Field(None, alias="serviceRemise")
    srv_montant: Optional[int] = Field(None, alias="srvMontant")
    infos_sup: Dict[str, str] = Field(default_factory=dict, alias="infosSup")

    def __init__(self, **data):
        super().__init__(**data)
        # Ensure infosSup is always a dict
        if self.infos_sup is None:
            self.infos_sup = {}


# ==================== MoyenExchange Schema ====================
class MoyenExchange(BaseModel):
    """
    Payment method exchange DTO
    Equivalent to Java MoyenExchange class
    """

    model_config = ConfigDict(populate_by_name=True)

    moyen_code: Optional[str] = Field(None, alias="moyenCode")
    moyen_type: Optional[str] = Field(None, alias="moyenType")
    infos_sup: Dict[str, str] = Field(default_factory=dict, alias="infosSup")


# ==================== TransactionExchange Schema ====================
class TransactionExchange(ExchangeAbstract):
    """
    Transaction exchange DTO for external partner calls
    Equivalent to Java TransactionExchange class

    This is the main DTO used for communication with external partners
    """

    model_config = ConfigDict(populate_by_name=True)

    service_exchange: Optional[ServiceExchange] = Field(None, alias="serviceExchange")
    moyen_exchange: Optional[MoyenExchange] = Field(None, alias="moyenExchange")
    transaction_montant: Optional[float] = Field(None, alias="transactionMontant")
    transaction_remise: Optional[float] = Field(None, alias="transactionRemise")

    def __repr__(self):
        return (f"TransactionExchange(service_exchange={self.service_exchange}, "
                f"moyen_exchange={self.moyen_exchange}, "
                f"transaction_montant={self.transaction_montant}, "
                f"transaction_remise={self.transaction_remise})")