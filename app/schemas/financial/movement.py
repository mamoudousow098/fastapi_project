from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List,Any ,Set
from datetime import datetime
from enum import Enum 

from app.core.base_model import CamelModel
from app.models import Flow


# ============================================================================
# CAP DTO
# ============================================================================


# ============================================================================
# ENUMS - Énumérations
# ============================================================================

class ISOCode(str, Enum):
    """Codes pays ISO"""
    SN = "SN"  # Sénégal
    FR = "FR"  # France
    CI = "CI"  # Côte d'Ivoire
    ML = "ML"  # Mali
    # Ajoutez d'autres codes selon vos besoins


class PIAccountType(str, Enum):
    """Types de comptes"""
    WALLET = "WALLET"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    MOBILE_MONEY = "MOBILE_MONEY"
    CARD = "CARD"


class ClientType(str, Enum):
    """Types de clients"""
    INDIVIDUAL = "INDIVIDUAL"
    CORPORATE = "CORPORATE"
    MERCHANT = "MERCHANT"


class IDSystem(str, Enum):
    """Systèmes d'identification"""
    NATIONAL_ID = "NATIONAL_ID"
    PASSPORT = "PASSPORT"
    DRIVER_LICENSE = "DRIVER_LICENSE"
    TAX_ID = "TAX_ID"


class TransactionStatus(str, Enum):
    """Statuts de transaction"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REVERSED = "REVERSED"


class StatusEnum(str, Enum):
    """Statuts généraux"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"


class TypeDocument(str, Enum):
    """Types de documents de référence"""
    INVOICE = "INVOICE"
    RECEIPT = "RECEIPT"
    CONTRACT = "CONTRACT"
    ORDER = "ORDER"


class RejectReason(str, Enum):
    """Raisons de rejet"""
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    INVALID_ACCOUNT = "INVALID_ACCOUNT"
    FRAUD_SUSPICION = "FRAUD_SUSPICION"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    TECHNICAL_ERROR = "TECHNICAL_ERROR"

class CapDTO(BaseModel):
    """DTO pour les données CAP (issuer/acquirer)"""
    code: Optional[str] = Field(None, description="Code CAP")
    name: Optional[str] = Field(None, description="Nom de l'entité")
    fees: Optional[float] = Field(None, description="Frais")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "CAP001",
                "name": "Main Issuer",
                "fees": 500.0
            }
        }
    )


# ============================================================================
# TRANSFER REQUEST MODEL
# ============================================================================

class TransferRequestModel(BaseModel):
    """
    Modèle de requête de transfert contenant tous les détails 
    pour initier un transfert financier
    """
    
    # Identifiants
    msg_id: Optional[str] = Field(None, description="Message identifier", example="MSG20241114001")
    end_to_end_id: Optional[str] = Field(None, description="End-to-end identifier for tracking", example="E2E20241114001")
    identifiant_transaction: Optional[str] = Field(None, description="Transaction identifier", example="TXN20241114001")
    
    # Montant
    montant: Optional[str] = Field(None, description="Transfer amount", example="50000.00")
    
    # Informations Payeur
    pays_client_payeur: Optional[ISOCode] = Field(None, description="Country code of payer client")
    type_compte_client_payeur: Optional[PIAccountType] = Field(None, description="Payer account type")
    devise_compte_client_payeur: Optional[str] = Field(None, description="Payer account currency", example="XOF")
    iban_client_payeur: Optional[str] = Field(None, description="Payer IBAN", example="SN08SN012345678901234567890")
    other_client_payeur: Optional[str] = Field(None, description="Other payer account identifier")
    alias_client_payeur: Optional[str] = Field(None, description="Payer alias or nickname")
    nom_client_payeur: Optional[str] = Field(None, description="Payer full name", example="Amadou Diallo")
    type_client_payeur: Optional[ClientType] = Field(None, description="Payer client type")
    code_membre_participant_payeur: Optional[str] = Field(None, description="Payer participant member code")
    
    # Identification Payeur
    numero_identification_client_payeur: Optional[str] = Field(None, description="Payer identification number")
    systeme_identification_client_payeur: Optional[IDSystem] = Field(None, description="Payer identification system")
    adresse_client_payeur: Optional[str] = Field(None, description="Payer address")
    ville_client_payeur: Optional[str] = Field(None, description="Payer city")
    latitude_client_payeur: Optional[str] = Field(None, description="Payer latitude coordinate")
    longitude_client_payeur: Optional[str] = Field(None, description="Payer longitude coordinate")
    
    # Données de naissance Payeur
    date_naissance_client_payeur: Optional[str] = Field(None, description="Payer date of birth")
    ville_naissance_client_payeur: Optional[str] = Field(None, description="Payer city of birth")
    pays_naissance_client_payeur: Optional[str] = Field(None, description="Payer country of birth")
    numero_rccm_client_payeur: Optional[str] = Field(None, description="Payer commercial registry number (RCCM)")
    
    # Informations Bénéficiaire
    code_membre_participant_paye: Optional[str] = Field(None, description="Payee participant member code")
    pays_client_paye: Optional[ISOCode] = Field(None, description="Country code of payee client")
    type_compte_client_paye: Optional[PIAccountType] = Field(None, description="Payee account type")
    devise_compte_client_paye: Optional[str] = Field(None, description="Payee account currency", example="XOF")
    iban_client_paye: Optional[str] = Field(None, description="Payee IBAN")
    other_client_paye: Optional[str] = Field(None, description="Other payee account identifier")
    nom_client_paye: Optional[str] = Field(None, description="Payee full name", example="Fatou Sow")
    type_client_paye: Optional[ClientType] = Field(None, description="Payee client type")
    alias_client_paye: Optional[str] = Field(None, description="Payee alias or nickname")
    
    # Identification Bénéficiaire
    numero_identification_client_paye: Optional[str] = Field(None, description="Payee identification number")
    systeme_identification_client_paye: Optional[IDSystem] = Field(None, description="Payee identification system")
    adresse_client_paye: Optional[str] = Field(None, description="Payee address")
    ville_client_paye: Optional[str] = Field(None, description="Payee city")
    latitude_client_paye: Optional[str] = Field(None, description="Payee latitude coordinate")
    longitude_client_paye: Optional[str] = Field(None, description="Payee longitude coordinate")
    
    # Données de naissance Bénéficiaire
    date_naissance_client_paye: Optional[str] = Field(None, description="Payee date of birth")
    ville_naissance_client_paye: Optional[str] = Field(None, description="Payee city of birth")
    pays_naissance_client_paye: Optional[str] = Field(None, description="Payee country of birth")
    numero_rccm_client_paye: Optional[str] = Field(None, description="Payee commercial registry number (RCCM)")
    
    # Détails de transaction
    canal_communication: Optional[str] = Field(None, description="Communication channel used", example="MOBILE_APP")
    date_heure_acceptation: Optional[str] = Field(None, description="Acceptance date and time")
    type_transaction: Optional[str] = Field(None, description="Transaction type", example="P2P_TRANSFER")
    motif: Optional[str] = Field(None, description="Transfer reason or purpose")
    
    # Documents et références
    reference_bulk: Optional[str] = Field(None, description="Bulk reference identifier")
    type_document_reference: Optional[TypeDocument] = Field(None, description="Reference document type")
    numero_document_reference: Optional[str] = Field(None, description="Reference document number")
    
    # Montants additionnels
    montant_achat: Optional[str] = Field(None, description="Purchase amount")
    montant_retrait: Optional[str] = Field(None, description="Withdrawal amount")
    frais_retrait: Optional[str] = Field(None, description="Withdrawal fees")
    
    # Demande de paiement
    client_demandeur: Optional[str] = Field(None, description="Requesting client identifier")
    identifiant_demande_paiement: Optional[str] = Field(None, description="Payment request identifier")
    
    # Dates limites
    date_heure_execution: Optional[str] = Field(None, description="Execution date and time")
    date_limite_action: Optional[str] = Field(None, description="Action deadline date")
    date_heure_limite_action: Optional[str] = Field(None, description="Action deadline date and time")
    
    # Raisons et retours
    raison: Optional[RejectReason] = Field(None, description="Rejection reason code")
    raison_retour: Optional[RejectReason] = Field(None, description="Return reason code")
    montant_retourne: Optional[str] = Field(None, description="Returned amount")
    
    # Remises
    autorisation_modification_montant: Optional[str] = Field(None, description="Authorization for amount modification")
    montant_remise_paiement_immediat: Optional[str] = Field(None, description="Immediate payment discount amount")
    taux_remise_paiement_immediat: Optional[str] = Field(None, description="Immediate payment discount rate")
    
    # Mandat
    identifiant_mandat: Optional[str] = Field(None, description="Mandate identifier")
    signature_numerique_mandat: Optional[str] = Field(None, description="Digital signature of mandate")
    
    # Rapports
    type_rapport: Optional[str] = Field(None, description="Report type")
    date_debut_periode: Optional[str] = Field(None, description="Period start date")
    heure_debut_periode: Optional[str] = Field(None, description="Period start time")
    
    # Autres
    legal_entity_code: Optional[str] = Field(None, description="Legal entity code")
    id: Optional[str] = Field(None, description="Unique identifier")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "msg_id": "MSG20241114001",
                "end_to_end_id": "E2E20241114001",
                "montant": "50000.00",
                "nom_client_payeur": "Amadou Diallo",
                "nom_client_paye": "Fatou Sow",
                "type_transaction": "P2P_TRANSFER"
            }
        }
    )


# ============================================================================
# TRANSFER RESPONSE MODEL
# ============================================================================

class TransferResponseModel(BaseModel):
    """
    Modèle de réponse de transfert contenant les résultats 
    d'exécution et le statut du transfert
    """
    
    # Identifiants
    msg_id: Optional[str] = Field(None, description="Message identifier")
    end_to_end_id: Optional[str] = Field(None, description="End-to-end identifier for tracking")
    msg_id_demande: Optional[str] = Field(None, description="Request message identifier")
    identifiant_transaction: Optional[str] = Field(None, description="Transaction identifier")
    
    # Statut et codes
    statut_transaction: Optional[TransactionStatus] = Field(None, description="Transaction status")
    statut: Optional[TransactionStatus] = Field(None, description="Status")
    code_raison: Optional[str] = Field(None, description="Reason code")
    code_service: Optional[str] = Field(None, description="Service code")
    
    # Dates
    date_heure_irrevocabilite: Optional[datetime] = Field(None, description="Irrevocability date and time")
    date_heure_acceptation: Optional[datetime] = Field(None, description="Acceptance date and time")
    
    # Informations additionnelles
    informations_additionnelles: Optional[str] = Field(None, description="Additional information")
    reference_bulk: Optional[str] = Field(None, description="Bulk reference identifier")
    
    # Montant
    montant: Optional[str] = Field(None, description="Transfer amount")
    
    # Informations Payeur (mêmes champs que TransferRequestModel)
    pays_client_payeur: Optional[ISOCode] = None
    type_compte_client_payeur: Optional[PIAccountType] = None
    devise_compte_client_payeur: Optional[str] = None
    iban_client_payeur: Optional[str] = None
    other_client_payeur: Optional[str] = None
    alias_client_payeur: Optional[str] = None
    nom_client_payeur: Optional[str] = None
    type_client_payeur: Optional[ClientType] = None
    code_membre_participant_payeur: Optional[str] = None
    numero_identification_client_payeur: Optional[str] = None
    systeme_identification_client_payeur: Optional[IDSystem] = None
    adresse_client_payeur: Optional[str] = None
    ville_client_payeur: Optional[str] = None
    latitude_client_payeur: Optional[str] = None
    longitude_client_payeur: Optional[str] = None
    date_naissance_client_payeur: Optional[str] = None
    ville_naissance_client_payeur: Optional[str] = None
    pays_naissance_client_payeur: Optional[str] = None
    numero_rccm_client_payeur: Optional[str] = None
    
    # Informations Bénéficiaire
    pays_client_paye: Optional[ISOCode] = None
    type_compte_client_paye: Optional[PIAccountType] = None
    devise_compte_client_paye: Optional[str] = None
    iban_client_paye: Optional[str] = None
    other_client_paye: Optional[str] = None
    nom_client_paye: Optional[str] = None
    type_client_paye: Optional[ClientType] = None
    alias_client_paye: Optional[str] = None
    numero_identification_client_paye: Optional[str] = None
    systeme_identification_client_paye: Optional[IDSystem] = None
    adresse_client_paye: Optional[str] = None
    ville_client_paye: Optional[str] = None
    latitude_client_paye: Optional[str] = None
    longitude_client_paye: Optional[str] = None
    date_naissance_client_paye: Optional[str] = None
    ville_naissance_client_paye: Optional[str] = None
    pays_naissance_client_paye: Optional[str] = None
    numero_rccm_client_paye: Optional[str] = None
    
    # Détails transaction
    canal_communication: Optional[str] = None
    type_transaction: Optional[str] = None
    motif: Optional[str] = None
    
    # Documents
    type_document_reference: Optional[TypeDocument] = None
    numero_document_reference: Optional[str] = None
    
    # Montants additionnels
    montant_achat: Optional[str] = None
    montant_retrait: Optional[str] = None
    frais_retrait: Optional[str] = None
    montant_retourne: Optional[str] = None
    
    # Demande de paiement
    identifiant_demande_paiement: Optional[str] = None
    date_limite_action: Optional[str] = None
    date_heure_limite_action: Optional[str] = None
    
    # Raisons
    raison: Optional[RejectReason] = None
    raison_retour: Optional[RejectReason] = None
    
    # Remises
    autorisation_modification_montant: Optional[str] = None
    montant_remise_paiement_immediat: Optional[str] = None
    taux_remise_paiement_immediat: Optional[str] = None
    
    # Mandat
    identifiant_mandat: Optional[str] = None
    signature_numerique_mandat: Optional[str] = None
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "msg_id": "MSG20241114001",
                "statut_transaction": "COMPLETED",
                "montant": "50000.00",
                "code_raison": "00"
            }
        }
    )


# ============================================================================
# MOVEMENT EXECUTION REQUEST
# ============================================================================

class MovementExecutionRequest(CamelModel):
    """
    Modèle de requête pour exécuter un mouvement/transaction financière
    """
    
    gu_id: Optional[str] = Field(
        None,
        description="Global Unique Identifier for the transaction",
        example="GU123456789"
    )
    
    otp: Optional[str] = Field(
        None,
        description="One-Time Password for transaction authentication",
        example="123456"
    )
    
    amount: Optional[float] = Field(
        None,
        description="Transaction amount",
        example=50000.00
    )
    
    partner_dist_id: Optional[str] = Field(
        None,
        description="Partner distributor identifier",
        example="DIST001"
    )
    
    legal_entity_code: str = Field(
        ...,
        description="Legal entity code",
        example="LE001"
    )
    
    product_code: Optional[str] = Field(
        None,
        description="Product code identifier",
        example="PROD001"
    )
    
    issuer_product_code: Optional[str] = Field(
        None,
        description="Issuer product code",
        example="ISS001"
    )
    
    acquirer_product_code: Optional[str] = Field(
        None,
        description="Acquirer product code",
        example="ACQ001"
    )
    
    reference_bulk: Optional[str] = Field(
        None,
        description="Reference for bulk transaction",
        example="BULK2024001"
    )
    
    ip_address: Optional[str] = Field(
        None,
        description="IP address of the client making the request",
        example="192.168.1.100"
    )
    
    agent_login: Optional[str] = Field(
        None,
        description="Agent login username",
        example="agent001"
    )
    
    user_agent: Optional[str] = Field(
        None,
        description="User agent string from the client",
        example="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )
    
    latitude: Optional[str] = Field(
        None,
        description="Latitude coordinate of transaction location",
        example="14.6928"
    )
    
    longitude: Optional[str] = Field(
        None,
        description="Longitude coordinate of transaction location",
        example="-17.4467"
    )
    
    callback_url: Optional[str] = Field(
        None,
        description="Callback URL for asynchronous response",
        example="https://partner.example.com/callback"
    )
    
    client_id: str = Field(
        ...,
        description="Client identifier",
        example="CLIENT001"
    )
    
    user_login: Optional[str] = Field(
        None,
        description="User login username",
        example="user001"
    )
    
    slip_number: Optional[str] = Field(
        None,
        description="Slip number for the transaction",
        example="SLIP2024001"
    )
    
    accounts_roles: Optional[Dict[str, str]] = Field(
        None,
        description="Map of account numbers with their respective roles",
        example={"source": "1234567890", "destination": "0987654321"}
    )
    
    service_code: str = Field(
        ...,
        description="Service code for the operation",
        example="SVC001"
    )
    
   
    
    account_number: Optional[str] = Field(
        None,
        description="Account number involved in the transaction",
        example="1234567890123"
    )
    
    bank_code: Optional[str] = Field(
        None,
        description="Bank code identifier",
        example="BNK001"
    )
    
    terminal_id: Optional[str] = Field(
        None,
        description="Terminal identifier",
        example="TERM001"
    )
    
    reason: Optional[str] = Field(
        None,
        description="Reason or description for the transaction",
        example="Payment for services"
    )
    
    asc_date: Optional[int] = Field(
        None,
        description="ASC date in timestamp format (milliseconds since epoch)",
        example=1731600000000
    )
    
    partner_id: Optional[str] = Field(
        None,
        description="Partner identifier",
        example="PARTNER001"
    )

    is_cancellation: Optional[bool] = Field(
        None,
        description="cancellation discrimination",
        example="True"
    )


    gu_id_cancellation: Optional[str] = Field(
        None,
        description="Global Unique Identifier for the transaction",
        example="GU123456789"
    )

    
    additional_informations: Optional[Dict[str, str]] = Field(
        None,
        description="Additional information as key-value pairs",
        example={"reference": "REF001", "note": "Special instructions"}
    )
    
    issuer_data: Optional[CapDTO] = Field(
        None,
        description="Issuer CAP data",
        json_schema_extra={"hidden": True}
    )
    
    acquirer_data: Optional[CapDTO] = Field(
        None,
        description="Acquirer CAP data",
        json_schema_extra={"hidden": True}
    )
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "legal_entity_code": "LE001",
                "client_id": "CLIENT001",
                "service_code": "SVC001",
                "amount": 50000.00,
                "account_number": "1234567890",
                "reason": "Payment for services"
            }
        }
    )


# ============================================================================
# RESPONSE DETAILS
# ============================================================================

# class ResponseDetails(CamelModel):
#     """
#     Informations de réponse détaillées contenant les codes de statut, 
#     messages et détails d'erreur
#     """
    
#     code: str = Field(
#         ...,
#         description="Response code indicating the result of the operation",
#         example="200"
#     )
    
#     status: Optional[StatusEnum] = Field(
#         None,
#         description="Status of the operation",
#         example="SUCCESS"
#     )
    
#     message: str = Field(
#         ...,
#         description="Human-readable message describing the result",
#         example="Transaction completed successfully"
#     )
    
#     errors: Optional[List[str]] = Field(
#         None,
#         description="List of error messages if any errors occurred",
#         example=["Invalid amount", "Insufficient balance"]
#     )
    
#     model_config = ConfigDict(
#         json_schema_extra={
#             "example": {
#                 "code": "200",
#                 "status": "SUCCESS",
#                 "message": "Transaction completed successfully",
#                 "errors": []
#             }
#         }
#     )

# class ResponseDetails(CamelModel):
#     """Schema for response details"""
#     code: str = Field(..., description="Response code")
#     message: str = Field(..., description="Response message/status")
#     is_error: bool = Field(False, description="Indicates if response is an error")
#     status: str = Field(..., description="status code")
#
#     model_config = ConfigDict(from_attributes=True)
#

class ResponseDetails(CamelModel):
    """
    Schema for response details
    Used for communicating operation results
    All fields are optional with None as default
    """

    # Status is the main status field (SUCCESS, FAILED, PENDING, etc.)
    status: Optional[str] = Field(None, description="Response status (SUCCESS, FAILED, PENDING, etc.)")

    # Code is optional and represents a more specific error/response code
    code: Optional[str] = Field(None, description="Specific response/error code")

    # Message provides details about the response
    message: Optional[str] = Field(None, description="Response message/details")

    # Indicates if this is an error response
    is_error: Optional[bool] = Field(None, description="Indicates if response is an error")

    # Optional: List of detailed errors (for validation errors, etc.)
    errors: Optional[List[str]] = Field(None, description="List of error messages")

    # Optional: Indicates if operation is asynchronous
    is_async: Optional[bool] = Field(None, description="Indicates if operation is async")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def success(cls, message: str = "Operation successful", **kwargs):
        """Create a success response"""
        return cls(
            status="SUCCESS",
            message=message,
            is_error=False,
            **kwargs
        )

    @classmethod
    def error(cls, code: str, message: str, **kwargs):
        """Create an error response"""
        return cls(
            status="FAILED",
            code=code,
            message=message,
            is_error=True,
            **kwargs
        )

    @classmethod
    def pending(cls, message: str = "Operation pending", **kwargs):
        """Create a pending response"""
        return cls(
            status="PENDING",
            message=message,
            is_error=False,
            **kwargs
        )

# ============================================================================
# MOVEMENT EXECUTION RESPONSE
# ============================================================================

class MovementExecutionResponse(CamelModel):
    """
    Modèle de réponse pour l'exécution de mouvement contenant 
    les détails de transaction et le statut
    """
    
    gu_id: Optional[str] = Field(
        None,
        description="Global Unique Identifier for the transaction",
        example="GU123456789"
    )
    
    legal_entity_code: Optional[str] = Field(
        None,
        description="Legal entity code",
        example="LE001"
    )
    
    service_code: Optional[str] = Field(
        None,
        description="Service code for the operation",
        example="SVC001"
    )
    
    client_id: Optional[str] = Field(
        None,
        description="Client identifier",
        example="CLIENT001"
    )
    
    amount: Optional[float] = Field(
        None,
        description="Transaction amount",
        example=50000.00
    )
    
    partner_dist_id: Optional[str] = Field(
        None,
        description="Partner distributor identifier",
        example="DIST001"
    )
    
    user_login: Optional[str] = Field(
        None,
        description="User login username",
        example="user001"
    )
    
    partner_id: Optional[str] = Field(
        None,
        description="Partner identifier",
        example="PARTNER001"
    )
    
    additional_informations: Optional[Dict[str, str]] = Field(
        None,
        description="Additional information as key-value pairs",
        example={"transactionRef": "TXN001", "timestamp": "2024-11-14T10:30:00Z"}
    )
    
    taxes: Optional[Dict[str, float]] = Field(
        None,
        description="Taxes information as key-value pairs",
        example={"TTC": 900.0, "TVA": 50.0}
    )
    
    discounts: Optional[Dict[str, float]] = Field(
        None,
        description="Discounts information as key-value pairs",
        example={"remise": 1000.0, "pourcentage": 2.0}
    )
    
    response_details: Optional[ResponseDetails] = Field(
        None,
        description="Detailed response information including status and error codes"
    )
    
    issuer_fees: Optional[float] = Field(None,
        description="Issuer fees for the transaction or movement",
        example=500.0
        )
    
    acquirer_fees: Optional[float] = Field(
        None,
        description="Acquirer fees for the transaction or movement",
        example=300.0
    )
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "gu_id": "GU123456789",
                "legal_entity_code": "LE001",
                "service_code": "SVC001",
                "client_id": "CLIENT001",
                "amount": 50000.00,
                "issuer_fees": 500.0,
                "acquirer_fees": 300.0,
                "response_details": {
                    "code": "200",
                    "status": "SUCCESS",
                    "message": "Transaction completed successfully"
                }
            }
        }
    )



""" 
     transfer_request_model: Optional[TransferRequestModel] = Field(
        None,
        description="Transfer request details"
    )
    
    transfer_response_model: Optional[TransferResponseModel] = Field(
        None,
        description="Transfer response details"
    ) """

class MovementExecutionBO(CamelModel):
    """
    Business object for movement execution.
    Python equivalent of Java MovementExecutionBO
    """
    
    # Core objects
    request: MovementExecutionRequest = Field(..., description="Movement execution request")
    movement: Optional[Any] = Field(None, description="Movement entity")
    response: Optional[MovementExecutionResponse] = Field(None, description="Movement execution response")
    response_details: Optional[ResponseDetails] = Field(None, description="Response details")
    
    # Status and change
    init_status: Optional[str] = Field(None, description="Initial status")
    change: Optional[Any] = Field(None, description="Change object")
    tag: Optional[str] = Field(None, description="Tag")
    change_tag: Optional[str] = Field(None, description="Change tag")
    
    # Service, flow, and product
    service: Optional[Any] = Field(None, description="Service entity")
    flow: Optional[Flow] = Field(None, description="Flow entity")
    product: Optional[Any] = Field(None, description="Product entity")
    legal_entity: Optional[Any] = Field(None, description="Legal entity")
    service_provider: Optional[Any] = Field(None, description="Service provider")
    
    # User and authentication
    kc_user: Optional[Dict[str, Any]] = Field(None, description="Keycloak user information")
    
    # Accounts management
    accounts: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Map of account roles to Account entities"
    )
    flow_account_roles: Optional[Set[str]] = Field(
        default_factory=set,
        description="Set of account roles required by the flow"
    )
    
    # Financial calculations
    total_amount_to_support_by_account: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Map of account numbers to total amounts they must support"
    )
    issuer_total_impact: Optional[float] = Field(0.0, description="Total impact for issuer")
    acquirer_total_impact: Optional[float] = Field(0.0, description="Total impact for acquirer")
    global_charge: Optional[float] = Field(0.0, description="Total charges")
    issuer_fees: Optional[float] = Field(0.0, description="Issuer fees")
    acquirer_fees: Optional[float] = Field(0.0, description="Acquirer fees")
    global_commission: Optional[float] = Field(0.0, description="Total commission")
    issuer_commission: Optional[float] = Field(0.0, description="Issuer commission")
    acquirer_commission: Optional[float] = Field(0.0, description="Acquirer commission")
    pending_movement_amount: float = Field(0.0, description="Pending movement amount")
    
    # Operations and validation
    can_create_operations: bool = Field(False, description="Whether operations can be created")
    
    # Parameters and configuration
    partner_url_parameter: Optional[Any] = Field(None, description="Partner URL parameter")
    
    # Flags for processing
    local_init: bool = Field(False, description="Whether this is a local initialization")
    recompute_operations: bool = Field(False, description="Whether to recompute operations")
    overdraft_issued: bool = Field(False, description="Whether overdraft was issued")
    
    # External service mapping
    service_mapping: Optional[Any] = Field(None, description="Service mapping for external calls")
    transaction_exchange: Optional[Any] = Field(None, description="Transaction exchange data")
    
    # Unique identifiers
    unique_partner_dist_id_value: Optional[str] = Field(
        None,
        description="Unique partner distribution ID value for duplicate check"
    )
    
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True
    )
    
    def get_response_from_request(self) -> MovementExecutionResponse:
        """
        Map the request data to a response object and include movement details.
        Equivalent to Java's getResponseFromRequest() using Dozer mapper.
        
        Returns:
            MovementExecutionResponse with data from request and movement
        """
        # Start with basic request data mapped to response
        response = MovementExecutionResponse(
            # Copy basic fields from request
            gu_id=self.request.gu_id,
            amount=self.request.amount,
            service_code=self.request.service_code,
            product_code=self.request.product_code,
            partner_id=self.request.partner_id,
            partner_dist_id=self.request.partner_dist_id,
            client_id=self.request.client_id,
            callback_url=self.request.callback_url,
            terminal_id=self.request.terminal_id,
            user_login=self.request.user_login,
            agent_login=self.request.agent_login,
            reason=self.request.reason,
            reference_bulk=self.request.reference_bulk,
            account_roles=self.request.accounts_roles,
            additional_informations=self.request.additional_informations,
            legal_entity_code=self.request.legal_entity_code,
            
            # Add response details
            response_details=self.response_details
        )
        return response