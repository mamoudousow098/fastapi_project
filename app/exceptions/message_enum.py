"""
Messages Enum for error codes and messages
Equivalent to Java MessagesEnum class
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class RejectReason(str, Enum):
    """Reject reason enumeration"""
    # Add your reject reasons here
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    INVALID_ACCOUNT = "INVALID_ACCOUNT"
    # Add more as needed


class MessagesEnum(Enum):
    """
    Messages enumeration with error codes and messages
    Equivalent to Java MessagesEnum
    """
    # Success codes (200-202)
    SUCCESS = (200, "Success", None)
    PART_SUCCESSFUL = (200, "Success", None)
    ALREADY_EXISTED = (201, "A movement with the same partnerDistID already exist", None)
    PENDING = (202, "The movement is in a pending state", None)
    PART_LOADED = (202, "The movement is in a pending state", None)
    FAILED = (400, "The movement failed", None)
    PART_FAILED = (400, "The movement failed", None)

    # Client errors (40001-40050)
    BAD_REQUEST = (40001, "Client error", None)
    ACCOUNTS_NOT_PROVIDED = (40002, "Accounts not provided", None)
    ACCOUNT_WITH_ROLE_NOT_FOUND = (40003, "Account with configured role not found in request", None)
    ISSUER_ACCOUNT_NOT_PROVIDED = (40004, "Issuer account not provided", None)
    USER_NOT_FOUND = (40005, "Cannot find user login in request", None)
    CANNOT_SAVE_MOVEMENT = (40006, "Cannot save movement", None)
    ISSUER_ACCOUNT_NOT_PROVIDED_FOR_CHECK = (40007, "Issuer account not provided for checking pending movements", None)
    ACQUIRER_ACCOUNT_NOT_PROVIDED = (40008, "Acquirer account not provided", None)

    # Forbidden errors (40301-40350)
    ELEMENT_NOT_ACTIVE = (40301, "Forbidden to access the resource", None)
    FLOW_INACTIVE = (40302, "Flow is inactive", None)
    NO_IMPACT_RULE_FOUND = (40303, "No impact rule found", None)
    NO_INTERVAL_RULE_FOUND = (40304, "No interval rule found", None)
    NO_MATCHING_INTERVAL_RULE_FOUND = (40305, "No matching interval rule found", None)
    ACCOUNT_INACTIVE = (40306, "Account is inactive", None)
    INSUFFICIENT_BALANCE = (40307, "Insufficient account balance", None)
    MOVEMENT_CANNOT_BE_LOADED = (40308, "This movement is not in the state to be loaded", None)
    DUPLICATED_MOVEMENT = (40309, "Movement with same IDs already exist", None)
    BALANCE_NOT_SUFFICIENT = (40310, "Balance not sufficient to perform this because of the pending transaction", None)
    NO_PROFILE_FOR_MOVEMENT = (40311, "No profile found to execute this movement", None)
    NO_TOKEN_FOUND = (40312, "No token found to execute this movement", None)
    SERVICE_INACTIVE = (40313, "Service inactive", None)
    MOVEMENT_CANNOT_BE_TERMINATED = (40314, "This movement is not in the state to be terminated", None)
    USER_NOT_MATCHED = (40315, "The user login in the request does not match the user login in the auth token", None)
    USER_NOT_ISSUER_OR_ACQUIRER = (40316, "The connected user is neither issuer nor acquirer", None)
    PROVIDER_NOT_CONFIGURED = (40317, "Provider not configured for EXTERNAL or PI service", None)
    NO_ACTIVE_PROVIDER_CONFIGURED = (40318, "No active provider configured for EXTERNAL or PI service", None)
    PROVIDER_ACCOUNT_NOT_CONFIGURED = (40319, "No provider account configured for EXTERNAL or PI service", None)
    SERVICE_SCOPE_NOT_FOUND = (40320, "Service scope not found", None)
    NO_MATCHING_EXTERNAL_SERVICE_CODE = (40321, "No matching external service code to map the EME service code", None)
    SAME_ISSUER_AND_ACQUIRER = (40322, "ISSUER account is the same as ACQUIRER account", None)
    MOVEMENT_CANNOT_BE_CANCELLED = (40323, "This movement is not in the state to be cancelled", None)
    MOVEMENT_CANCELLATION_CANNOT_BE_REJECTED = (40324, "Movement cancellation cannot be rejected", None)
    MOVEMENT_CANNOT_BE_REJECTED = (40325, "Movement cannot be rejected", None)
    NO_CONSTRAINT_CONFIGURED = (40326, "No constraint value configured", None)
    DUPLICATED_MOVEMENT_PARTNER_DIST_ID = (40327, "A Pending Movement with same PartnerDistID already exist", None)
    CODE_OTP_NOT_VALID = (40328, "OTP is not valid", None)
    CODE_OTP_CHANNEL_NOT_VALID = (40329, "OTP Channel is not valid", None)
    ADDITIONAL_INFO_NOT_PROVIDED = (40330, "Additional info not provided", None)
    CODE_OTP_OR_CHANNEL_NOT_PROVIDED = (40331, "OTP or Channel Not provided", None)
    MOVEMENT_NOT_ALLOWED = (40332, "movement not allowed", None)
    LEGAL_ENTITY_MISMATCH = (40333, "Cannot link this account for this service", None)
    DUPLICATED_MOVEMENT_IN_LAST_MN = (40334, "Duplicated movement , a same movement has been initiated in last last  mn", None)
    PROVIDER_INACTIVE = (40335, "Provider inactive", None)
    ACCOUNT_BLOCKED = (40336, "Account blocked", None)
    ACCOUNT_FROZEN = (40337, "Account frozen", None)
    ACCOUNT_SUSPENDED = (40338, "Account suspended", None)
    CLIENT_BLOCKED = (40339, "Client blocked", None)
    CLIENT_INACTIVE = (40340, "Client inactive", None)
    INSUFFICIENT_KYC_LEVEL_FOR_PRODUCT = (40341, "Insufficient kyc level for using product", None)
    INSUFFICIENT_KYC_LEVEL_FOR_SERVICE = (40342, "Insufficient kyc level for using service", None)
    NOT_THE_SAME_AMOUNT = (40343, "The amount in executionRequest and the amount in transfer request are different", None)
    NOT_SAME_ISSUER_AND_ACQUIRER = (40344, "ISSUER account is not the same as ACQUIRER account", None)
    MOVEMENT_CANNOT_BE_RESTORED = (40345, "Movement cannot be restored", None)
    USER_NOT_ISSUER = (40346, "The connected user is not the issuer", None)
    MOVEMENT_ALREADY_REJECTED = (40347, "Movement already rejected", None)
    MOVEMENT_CANCELLATION_CANNOT_BE_LOADED = (40348, "This movement cancellation is not in the state to be loaded", None)
    MOVEMENT_ALREADY_CANCELLED = (40349, "Movement already cancelled", None)
    CANCELLATION_ALREADY_REJECTED = (40350, "Movement already cancelled", None)

    # Not found errors (40401-40414)
    ELEMENT_NOT_FOUND = (40401, "Cannot find the resource", None)
    FLOW_NOT_FOUND = (40402, "No active flow found", None)
    ACCOUNT_NOT_FOUND = (40403, "Account not found", None)
    NO_ACCOUNT_TYPE_FOUND_FOR_ACCOUNT = (40404, "No account type found for account", None)
    NO_MATCHING_ACCOUNT_TYPE_FOUND_FOR_ROLE = (40405, "No matching account type found for role and account", None)
    MOVEMENT_NOT_FOUND = (40406, "Cannot find movement with provided GU ID", None)
    STATUS_NOT_FOUND = (40407, "Movement status not found", None)
    LEGAL_ENTITY_NOT_FOUND = (40408, "Legal entity not found", None)
    CONSTRAINT_NOT_IMPLEMENTED = (40409, "Constraint not implemented", None)
    SERVICE_NOT_FOUND = (40410, "Service not found", None)
    INVALID_AMOUNT = (40411, "Amount is invalid", None)
    DUPLICATED_IMPACT = (40412, "Duplicated impact", None)
    CANNOT_RECOMPUTE = (40413, "Cannot recompute impacts based on flow", None)
    PRODUCT_NOT_FOUND = (40414, "Product not found", None)
    ALIAS_NOT_FOUND = (40414, "alias not found", None)

    # Server errors (50001-50300)
    SERVER_ERROR = (50001, "Unknown server error", None)
    OPERATIONS_CREATION_ERROR = (50002, "An error occurred while creating operations", None)
    OPERATIONS_NOT_FOUND = (50003, "Cannot find operations saved in movement", None)
    SERVICE_URL_NOT_FOUND = (50004, "Cannot find service URL to execute external movement", None)
    PARAMETER_NOT_FOUND = (50005, "Cannot find parameter", None)
    ACCOUNT_KYC_BALANCE_LIMIT = (50006, "You have reached your balance limit", None)
    ACCOUNT_KYC_DAILY_CAP_LIMIT = (50007, "You have reached your maximum daily amount", None)
    ACCOUNT_KYC_MONTHLY_CAP_LIMIT = (50008, "You have reached your maximum monthly amount", None)
    INVALID_PROJECT_TOPIC_FORMAT = (50009, "Invalid project:topic format for Pub/Sub", None)
    MAINTENANCE = (50300, "The Unified Financial Platform is unavailable. Please try again later.", None)

    def __init__(self, error_code: int, error_message: str, reject_reason: Optional[RejectReason]):
        self._error_code = error_code
        self._error_message = error_message
        self._reject_reason = reject_reason

    @property
    def error_code(self) -> int:
        """Get error code"""
        return self._error_code

    @property
    def error_message(self) -> str:
        """Get error message"""
        return self._error_message

    @property
    def reject_reason(self) -> Optional[RejectReason]:
        """Get reject reason"""
        return self._reject_reason

    @classmethod
    def find_by_error_code(cls, error_code: int) -> Optional['MessagesEnum']:
        """
        Find MessagesEnum by error code

        Args:
            error_code: Error code to search for

        Returns:
            MessagesEnum instance or None if not found
        """
        for message in cls:
            if message.error_code == error_code:
                return message
        return None

    @classmethod
    def find_by_name(cls, name: str) -> Optional['MessagesEnum']:
        """
        Find MessagesEnum by name

        Args:
            name: Enum name to search for

        Returns:
            MessagesEnum instance or None if not found
        """
        try:
            return cls[name]
        except KeyError:
            return None

    def __str__(self) -> str:
        return f"{self.name}: {self.error_message} (code: {self.error_code})"

    def __repr__(self) -> str:
        return f"MessagesEnum.{self.name}"


# Pydantic model for API responses
class ErrorResponse(BaseModel):
    """
    Error response model for API
    """
    error_code: int
    error_message: str
    message_enum: Optional[str] = None
    reject_reason: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": 40403,
                "error_message": "Account not found",
                "message_enum": "ACCOUNT_NOT_FOUND",
                "reject_reason": None
            }
        }

    @classmethod
    def from_messages_enum(cls, message_enum: MessagesEnum) -> 'ErrorResponse':
        """
        Create ErrorResponse from MessagesEnum

        Args:
            message_enum: MessagesEnum instance

        Returns:
            ErrorResponse instance
        """
        return cls(
            error_code=message_enum.error_code,
            error_message=message_enum.error_message,
            message_enum=message_enum.name,
            reject_reason=message_enum.reject_reason.value if message_enum.reject_reason else None
        )


# Usage examples
if __name__ == "__main__":
    # Access enum values
    print(MessagesEnum.SUCCESS.error_code)  # 200
    print(MessagesEnum.SUCCESS.error_message)  # "Success"

    # Find by error code
    message = MessagesEnum.find_by_error_code(40403)
    print(message)  # MessagesEnum.ACCOUNT_NOT_FOUND

    # Find by name
    message = MessagesEnum.find_by_name("ACCOUNT_NOT_FOUND")
    print(message.error_message)  # "Account not found"

    # Create error response
    error = ErrorResponse.from_messages_enum(MessagesEnum.ACCOUNT_NOT_FOUND)
    print(error.model_dump_json())