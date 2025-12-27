import enum


class EntityState(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class CommissionBaseEnum(str, enum.Enum):
    NOMINAL_AMOUNT = "NOMINAL_AMOUNT"
    TRANSACTION_AMOUNT = "TRANSACTION_AMOUNT"
    FEES_AMOUNT = "FEES_AMOUNT"


class MovementTypeEnum(str, enum.Enum):
    OPERATION = "OPERATION"
    TRANSACTION = "TRANSACTION"


class ServiceFlow(str, enum.Enum):
    ENCAISSEMENT = "ENCAISSEMENT"
    DECAISSEMENT = "DECAISSEMENT"


class ServiceScope(str, enum.Enum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
    PI = "PI"

# --- ENUMS ---
class AccountCategory(str,enum.Enum):
    EME = "EME"
    DISTRIBUTOR = "DISTRIBUTOR"
    CUSTOMER = "CUSTOMER"
    CORPORATE = "CORPORATE"

class AccountPrefix(str,enum.Enum):
    SUB_ACCOUNT = "SUB_ACCOUNT"
    ACCOUNT = "ACCOUNT"


class OperationDirection(str, enum.Enum):
    """Direction de l'opération"""
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class MovementContext(str, enum.Enum):
    """Contexte du mouvement"""
    INITIATION = "INITIATION"
    VALIDATION = "VALIDATION"


class ConstraintType(str, enum.Enum):
    """Types de contraintes"""
    CHECK_PENDING_MOVEMENT_AMOUNT = "CHECK_PENDING_MOVEMENT_AMOUNT"
    CHECK_PROFILE_HAS_ROLE = "CHECK_PROFILE_HAS_ROLE"
    CHECK_ISSUER_OTP = "CHECK_ISSUER_OTP"
    CHECK_NOMBO = "CHECK_NOMBO"
    
    @property
    def description(self) -> str:
        """Retourne la description de la contrainte"""
        descriptions = {
            self.CHECK_PENDING_MOVEMENT_AMOUNT: "Check if the total amount of all the pending transactions for cash out is less than the account balance",
            self.CHECK_PROFILE_HAS_ROLE: "Check if the profile has a certain role",
            self.CHECK_ISSUER_OTP: "Check if the issuer has valid OTP",
            self.CHECK_NOMBO: "checking the movement to Nombo"
        }
        return descriptions.get(self, "")


class Gateway(str, enum.Enum):
    """Types de gateway"""
    USSD = "USSD"
    APIDIST = "APIDIST"
    CONNECTOR = "CONNECTOR"