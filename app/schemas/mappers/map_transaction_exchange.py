# """
# Mapper for converting MovementExecutionBO to TransactionExchange
# Equivalent to Java MapTransactionExchangeToMovementRequest class
# """
# import logging
# import json
# from urllib.parse import quote
# from typing import Dict, Optional
# from decimal import Decimal
#
# from app.schemas.transaction_exchange import TransactionExchange, ServiceExchange
# from app.services.movement import BrokerException
# from app.services.parameter import ParameterService
# from app.services.account_mapping import AccountMappingService
# #from app.exceptions import BrokerException, MessagesEnum
#
# logger = logging.getLogger(__name__)
#
#
# class Constants:
#     """Constants for mapper"""
#     ACQUIRER_ACCOUNT_ROLE = "ACQUIRER"
#     ISSUER_ACCOUNT_ROLE = "ISSUER"
#     _AGENT_LOGIN_GU1 = "_AGENT_LOGIN_GU1"
#     _AGENCY_CODE_GU1 = "_AGENCY_CODE_GU1"
#     _PDA_CODE_GU1 = "_PDA_CODE_GU1"
#     CALLBACK_URL_EME = "CALLBACK_URL_EME"
#
#
# class MapTransactionExchangeToMovementRequest:
#     """
#     Mapper class for converting internal requests to external partner format
#     Equivalent to Java MapTransactionExchangeToMovementRequest
#     """
#
#     # Cache for frequently accessed parameters
#     _agent_logins: Dict[str, str] = {}
#     _agency_codes: Dict[str, str] = {}
#     _pda_codes: Dict[str, str] = {}
#     _callback_url: Optional[str] = None
#
#     #def __init__(self, parameter_service: ParameterService, account_mapping_service: AccountMappingService):
#     def __init__(self):
#         self.parameter_service = ParameterService
#         self.account_mapping_service = AccountMappingService
#
#     @staticmethod
#     def movement_exchange_to_transaction_exchange(execution_bo) -> TransactionExchange:
#         """
#         Convert MovementExecutionBO to TransactionExchange
#
#         Args:
#             execution_bo: MovementExecutionBO object
#
#         Returns:
#             TransactionExchange object ready for external partner
#         """
#         logger.debug("Converting movement to transaction exchange")
#
#         # Create service exchange
#         service_exchange = ServiceExchange()
#
#         # Set infos_sup (additional information)
#         if execution_bo.request.additional_informations:
#             service_exchange.infos_sup = execution_bo.request.additional_informations.copy()
#         else:
#             service_exchange.infos_sup = {}
#
#         # Add destinataire (recipient)
#         service_exchange.infos_sup["destinataire"] = execution_bo.movement.client_id
#
#         # Set service code
#         service_exchange.service_code = execution_bo.movement.service_code
#
#         # Create transaction exchange
#         transaction_exchange = TransactionExchange(
#             service_exchange=service_exchange,
#             transaction_montant=execution_bo.movement.amount,
#             token=execution_bo.movement.gu_id,
#             login_agent=execution_bo.request.agent_login
#         )
#
#         logger.debug(f"Transaction exchange created for movement: {execution_bo.movement.gu_id}")
#         return transaction_exchange
#
#     def add_additional_infos_for_ussd(
#             self,
#             execution_bo,
#             exchange: TransactionExchange
#     ) -> None:
#         """
#         Add additional information for USSD gateway
#
#         Args:
#             execution_bo: MovementExecutionBO object
#             exchange: TransactionExchange to update
#
#         Raises:
#             BrokerException: If required parameters are not found
#         """
#         logger.debug("Adding additional info for USSD gateway")
#
#         country_iso_code = execution_bo.movement.country_iso_code
#
#         # Add product codes
#         exchange.service_exchange.infos_sup["productCode"] = "API"
#         exchange.service_exchange.infos_sup["codeProduit"] = "PDA"
#
#         # Add callback URL
#         callback_url = self._get_callback_url()
#         exchange.service_exchange.infos_sup["call_back_url"] = callback_url
#
#         # Add partner distribution transaction ID
#         agency_code = self._get_agency_code(country_iso_code)
#         partner_dist_id = f"{agency_code}_{execution_bo.movement.gu_id}"
#         exchange.service_exchange.infos_sup["partner_dist_transaction_id"] = partner_dist_id
#
#         # Set agent login
#         agent_login = self._get_agent_login(country_iso_code)
#         exchange.login_agent = agent_login
#
#         # Set PDA code
#         pda_code = self._get_pda_code(country_iso_code)
#         exchange.code_pda = pda_code
#
#         # Set sale point code
#         exchange.sale_point_code = agency_code
#
#         logger.debug(f"USSD info added: agent={agent_login}, agency={agency_code}, pda={pda_code}")
#
#     def add_additional_infos_for_connector(
#             self,
#             execution_bo,
#             exchange: TransactionExchange
#     ) -> None:
#         """
#         Add additional information for CONNECTOR gateway
#
#         Args:
#             execution_bo: MovementExecutionBO object
#             exchange: TransactionExchange to update
#
#         Raises:
#             BrokerException: If required data is not available
#         """
#         logger.debug("Adding additional info for CONNECTOR gateway")
#
#         # Add currency information
#         if (exchange.service_exchange.infos_sup.get("indicatifPIAg") is None and
#                 execution_bo.service and
#                 execution_bo.service.legal_entity and
#                 execution_bo.service.legal_entity.country):
#
#             country = execution_bo.service.legal_entity.country
#             exchange.service_exchange.infos_sup["indicatifPIAg"] = str(country.area_code)
#             exchange.service_exchange.infos_sup["codePIAg"] = country.iso_code
#             exchange.service_exchange.infos_sup["currencyPIAg"] = country.currency
#             exchange.service_exchange.infos_sup["numCurrencyPIAg"] = country.currency_number
#
#             logger.debug(f"Currency info added: {country.iso_code} - {country.currency}")
#
#         # Add sale point information
#         account_number = self._get_account_number(execution_bo.movement.account_roles)
#
#         if account_number:
#             account_mapping = self.account_mapping_service.get_by_code_gu3(account_number)
#
#             if account_mapping:
#                 exchange.sale_point_code = account_mapping.code_gu1
#                 logger.debug(f"Sale point code mapped: {account_number} -> {account_mapping.code_gu1}")
#             else:
#                 exchange.sale_point_code = account_number
#                 logger.debug(f"Sale point code set directly: {account_number}")
#         else:
#             logger.warning("No account number found for sale point code")
#
#     @staticmethod
#     def _get_account_number(account_roles: Dict[str, str]) -> Optional[str]:
#         """
#         Get account number from account roles
#         Priority: ACQUIRER > ISSUER
#
#         Args:
#             account_roles: Dictionary of account roles
#
#         Returns:
#             Account number or None
#         """
#         if account_roles.get(Constants.ACQUIRER_ACCOUNT_ROLE):
#             return account_roles[Constants.ACQUIRER_ACCOUNT_ROLE]
#         elif account_roles.get(Constants.ISSUER_ACCOUNT_ROLE):
#             return account_roles[Constants.ISSUER_ACCOUNT_ROLE]
#         return None
#
#     @staticmethod
#     def get_connector_url_context(execution_bo, transaction_exchange: TransactionExchange) -> str:
#         """
#         Build URL context for connector gateway GET requests
#
#         Args:
#             execution_bo: MovementExecutionBO object
#             transaction_exchange: TransactionExchange object
#
#         Returns:
#             URL context string with encoded parameters
#         """
#         logger.debug("Building connector URL context")
#
#         # Determine if we need a leading slash
#         base_url = execution_bo.partner_url_parameter.prm_string_value
#         context = "" if base_url.endswith("/") else "/"
#
#         # Build URL path with encoded parameters
#         client_id_encoded = quote(execution_bo.movement.client_id, safe='')
#         amount_formatted = MapTransactionExchangeToMovementRequest._format_decimal(
#             execution_bo.movement.amount
#         )
#
#         # Encode transaction exchange as JSON
#         exchange_json = json.dumps(transaction_exchange.dict(by_alias=True))
#         exchange_encoded = quote(exchange_json, safe='')
#
#         context += (
#             f"{execution_bo.service_mapping.code_gu1}/"
#             f"{client_id_encoded}/"
#             f"{amount_formatted}"
#             f"?exchange={exchange_encoded}"
#         )
#
#         logger.debug(f"Connector URL context built: {context[:100]}...")
#         return context
#
#     @staticmethod
#     def _format_decimal(value: float) -> str:
#         """
#         Format decimal number without trailing zeros
#         Equivalent to Java DecimalFormat("0.#")
#
#         Args:
#             value: Decimal value to format
#
#         Returns:
#             Formatted string
#         """
#         # Convert to Decimal for precise formatting
#         decimal_value = Decimal(str(value))
#         # Normalize to remove trailing zeros
#         normalized = decimal_value.normalize()
#         # Convert to string
#         return str(normalized)
#
#     def _get_agent_login(self, country_iso_code: str) -> str:
#         """Get agent login from cache or database"""
#         cache_key = f"{country_iso_code}{Constants._AGENT_LOGIN_GU1}"
#
#         if cache_key not in self._agent_logins:
#             parameter = self.parameter_service.get_parameter_by_code(cache_key)
#             if not parameter:
#                 raise BrokerException(
#                     "MessagesEnum.PARAMETER_NOT_FOUND",
#                     f"Parameter not found: {cache_key}"
#                 )
#             self._agent_logins[cache_key] = parameter.prm_string_value
#             logger.debug(f"Cached agent login for {country_iso_code}")
#
#         return self._agent_logins[cache_key]
#
#     def _get_agency_code(self, country_iso_code: str) -> str:
#         """Get agency code from cache or database"""
#         cache_key = f"{country_iso_code}{Constants._AGENCY_CODE_GU1}"
#
#         if cache_key not in self._agency_codes:
#             parameter = self.parameter_service.get_parameter_by_code(cache_key)
#             if not parameter:
#                 raise BrokerException(
#                     "MessagesEnum.PARAMETER_NOT_FOUND",
#                     f"Parameter not found: {cache_key}"
#                 )
#             self._agency_codes[cache_key] = parameter.prm_string_value
#             logger.debug(f"Cached agency code for {country_iso_code}")
#
#         return self._agency_codes[cache_key]
#
#     def _get_pda_code(self, country_iso_code: str) -> str:
#         """Get PDA code from cache or database"""
#         cache_key = f"{country_iso_code}{Constants._PDA_CODE_GU1}"
#
#         if cache_key not in self._pda_codes:
#             parameter = self.parameter_service.get_parameter_by_code(cache_key)
#             if not parameter:
#                 raise BrokerException(
#                     "MessagesEnum.PARAMETER_NOT_FOUND",
#                     f"Parameter not found: {cache_key}"
#                 )
#             self._pda_codes[cache_key] = parameter.prm_string_value
#             logger.debug(f"Cached PDA code for {country_iso_code}")
#
#         return self._pda_codes[cache_key]
#
#     def _get_callback_url(self) -> str:
#         """Get callback URL from cache or database"""
#         if self._callback_url is None:
#             parameter = self.parameter_service.get_parameter_by_code(Constants.CALLBACK_URL_EME)
#             if not parameter:
#                 raise BrokerException(
#                     "MessagesEnum.PARAMETER_NOT_FOUND",
#                     f"Parameter not found: {Constants.CALLBACK_URL_EME}"
#                 )
#             self._callback_url = parameter.prm_string_value
#             logger.debug("Cached callback URL")
#
#         return self._callback_url
#
#     @classmethod
#     def clear_cache(cls):
#         """Clear all cached parameters"""
#         cls._agent_logins.clear()
#         cls._agency_codes.clear()
#         cls._pda_codes.clear()
#         cls._callback_url = None
#         logger.info("Mapper cache cleared")

"""
Fixed mapper with proper service initialization
"""
import logging
import json
from urllib.parse import quote
from typing import Dict, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from app.schemas.transaction_exchange import TransactionExchange, ServiceExchange
from app.services.movement_checker import BrokerException
from app.services.parameter import ParameterService
from app.services.account_mapping import AccountMappingService

logger = logging.getLogger(__name__)


class Constants:
    """Constants for mapper"""
    ACQUIRER_ACCOUNT_ROLE = "ACQUIRER"
    ISSUER_ACCOUNT_ROLE = "ISSUER"
    _AGENT_LOGIN_GU1 = "_AGENT_LOGIN_GU1"
    _AGENCY_CODE_GU1 = "_AGENCY_CODE_GU1"
    _PDA_CODE_GU1 = "_PDA_CODE_GU1"
    CALLBACK_URL_EME = "CALLBACK_URL_EME"


class MapTransactionExchangeToMovementRequest:
    """
    Mapper class for converting internal requests to external partner format
    Equivalent to Java MapTransactionExchangeToMovementRequest
    """

    # Cache for frequently accessed parameters
    _agent_logins: Dict[str, str] = {}
    _agency_codes: Dict[str, str] = {}
    _pda_codes: Dict[str, str] = {}
    _callback_url: Optional[str] = None

    def __init__(self, db: Session):
        """
        Initialize mapper with database session

        Args:
            db: SQLAlchemy database session
        """
        # ✅ CORRECT: Create instances of services
        self.parameter_service = ParameterService(db)
        self.account_mapping_service = AccountMappingService(db)

    @staticmethod
    def movement_exchange_to_transaction_exchange(execution_bo) -> TransactionExchange:
        """
        Convert MovementExecutionBO to TransactionExchange

        Args:
            execution_bo: MovementExecutionBO object

        Returns:
            TransactionExchange object ready for external partner
        """
        logger.debug("Converting movement to transaction exchange")

        # Create service exchange
        service_exchange = ServiceExchange()

        # Set infos_sup (additional information)
        if execution_bo.request.additional_informations:
            service_exchange.infos_sup = execution_bo.request.additional_informations.copy()
        else:
            service_exchange.infos_sup = {}

        # Add destinataire (recipient)
        service_exchange.infos_sup["destinataire"] = execution_bo.movement.client_id

        # Set service code
        service_exchange.service_code = execution_bo.movement.service_code

        # Create transaction exchange
        transaction_exchange = TransactionExchange(
            service_exchange=service_exchange,
            transaction_montant=execution_bo.movement.amount,
            token=execution_bo.movement.gu_id,
            login_agent=execution_bo.request.agent_login
        )

        logger.debug(f"Transaction exchange created for movement: {execution_bo.movement.gu_id}")
        return transaction_exchange

    def add_additional_infos_for_ussd(
            self,
            execution_bo,
            exchange: TransactionExchange
    ) -> None:
        """
        Add additional information for USSD gateway

        Args:
            execution_bo: MovementExecutionBO object
            exchange: TransactionExchange to update

        Raises:
            BrokerException: If required parameters are not found
        """
        logger.debug("Adding additional info for USSD gateway")

        country_iso_code = execution_bo.movement.country_iso_code

        # Add product codes
        exchange.service_exchange.infos_sup["productCode"] = "API"
        exchange.service_exchange.infos_sup["codeProduit"] = "PDA"

        # Add callback URL
        callback_url = self._get_callback_url()
        exchange.service_exchange.infos_sup["call_back_url"] = callback_url

        # Add partner distribution transaction ID
        agency_code = self._get_agency_code(country_iso_code)
        partner_dist_id = f"{agency_code}_{execution_bo.movement.gu_id}"
        exchange.service_exchange.infos_sup["partner_dist_transaction_id"] = partner_dist_id

        # Set agent login
        agent_login = self._get_agent_login(country_iso_code)
        exchange.login_agent = agent_login

        # Set PDA code
        pda_code = self._get_pda_code(country_iso_code)
        exchange.code_pda = pda_code

        # Set sale point code
        exchange.sale_point_code = agency_code

        logger.debug(f"USSD info added: agent={agent_login}, agency={agency_code}, pda={pda_code}")

    def add_additional_infos_for_connector(
            self,
            execution_bo,
            exchange: TransactionExchange
    ) -> None:
        """
        Add additional information for CONNECTOR gateway

        Args:
            execution_bo: MovementExecutionBO object
            exchange: TransactionExchange to update

        Raises:
            BrokerException: If required data is not available
        """
        logger.debug("Adding additional info for CONNECTOR gateway")

        # Add currency information
        if (exchange.service_exchange.infos_sup.get("indicatifPIAg") is None and
                execution_bo.service and
                execution_bo.service.legal_entity and
                execution_bo.service.legal_entity.country):

            country = execution_bo.service.legal_entity.country
            exchange.service_exchange.infos_sup["indicatifPIAg"] = str(country.area_code)
            exchange.service_exchange.infos_sup["codePIAg"] = country.iso_code
            exchange.service_exchange.infos_sup["currencyPIAg"] = country.currency
            exchange.service_exchange.infos_sup["numCurrencyPIAg"] = country.currency_number

            logger.debug(f"Currency info added: {country.iso_code} - {country.currency}")

        # Add sale point information
        account_number = self._get_account_number(execution_bo.movement.account_roles)

        if account_number:
            # ✅ CORRECT: Use instance method
            account_mapping = self.account_mapping_service.get_by_code_gu3(account_number)

            if account_mapping:
                exchange.sale_point_code = account_mapping.code_gu1
                logger.debug(f"Sale point code mapped: {account_number} -> {account_mapping.code_gu1}")
            else:
                exchange.sale_point_code = account_number
                logger.debug(f"Sale point code set directly: {account_number}")
        else:
            logger.warning("No account number found for sale point code")

    @staticmethod
    def _get_account_number(account_roles: Dict[str, str]) -> Optional[str]:
        """
        Get account number from account roles
        Priority: ACQUIRER > ISSUER

        Args:
            account_roles: Dictionary of account roles

        Returns:
            Account number or None
        """
        if account_roles.get(Constants.ACQUIRER_ACCOUNT_ROLE):
            return account_roles[Constants.ACQUIRER_ACCOUNT_ROLE]
        elif account_roles.get(Constants.ISSUER_ACCOUNT_ROLE):
            return account_roles[Constants.ISSUER_ACCOUNT_ROLE]
        return None

    @staticmethod
    def get_connector_url_context(execution_bo, transaction_exchange: TransactionExchange) -> str:
        """
        Build URL context for connector gateway GET requests

        Args:
            execution_bo: MovementExecutionBO object
            transaction_exchange: TransactionExchange object

        Returns:
            URL context string with encoded parameters
        """
        logger.debug("Building connector URL context")

        # Determine if we need a leading slash
        base_url = execution_bo.partner_url_parameter.prm_string_value
        context = "" if base_url.endswith("/") else "/"

        # Build URL path with encoded parameters
        client_id_encoded = quote(execution_bo.movement.client_id, safe='')
        amount_formatted = MapTransactionExchangeToMovementRequest._format_decimal(
            execution_bo.movement.amount
        )

        # Encode transaction exchange as JSON
        exchange_json = json.dumps(transaction_exchange.dict(by_alias=True))
        exchange_encoded = quote(exchange_json, safe='')

        context += (
            f"{execution_bo.service_mapping.code_gu1}/"
            f"{client_id_encoded}/"
            f"{amount_formatted}"
            f"?exchange={exchange_encoded}"
        )

        logger.debug(f"Connector URL context built: {context[:100]}...")
        return context

    @staticmethod
    def _format_decimal(value: float) -> str:
        """
        Format decimal number without trailing zeros
        Equivalent to Java DecimalFormat("0.#")

        Args:
            value: Decimal value to format

        Returns:
            Formatted string
        """
        # Convert to Decimal for precise formatting
        decimal_value = Decimal(str(value))
        # Normalize to remove trailing zeros
        normalized = decimal_value.normalize()
        # Convert to string
        return str(normalized)

    def _get_agent_login(self, country_iso_code: str) -> str:
        """Get agent login from cache or database"""
        cache_key = f"{country_iso_code}{Constants._AGENT_LOGIN_GU1}"

        if cache_key not in self._agent_logins:
            parameter = self.parameter_service.get_parameter_by_code(cache_key)
            if not parameter:
                raise BrokerException(
                    "MessagesEnum.PARAMETER_NOT_FOUND",
                    f"Parameter not found: {cache_key}"
                )
            self._agent_logins[cache_key] = parameter.prm_string_value
            logger.debug(f"Cached agent login for {country_iso_code}")

        return self._agent_logins[cache_key]

    def _get_agency_code(self, country_iso_code: str) -> str:
        """Get agency code from cache or database"""
        cache_key = f"{country_iso_code}{Constants._AGENCY_CODE_GU1}"

        if cache_key not in self._agency_codes:
            parameter = self.parameter_service.get_parameter_by_code(cache_key)
            if not parameter:
                raise BrokerException(
                    "MessagesEnum.PARAMETER_NOT_FOUND",
                    f"Parameter not found: {cache_key}"
                )
            self._agency_codes[cache_key] = parameter.prm_string_value
            logger.debug(f"Cached agency code for {country_iso_code}")

        return self._agency_codes[cache_key]

    def _get_pda_code(self, country_iso_code: str) -> str:
        """Get PDA code from cache or database"""
        cache_key = f"{country_iso_code}{Constants._PDA_CODE_GU1}"

        if cache_key not in self._pda_codes:
            parameter = self.parameter_service.get_parameter_by_code(cache_key)
            if not parameter:
                raise BrokerException(
                    "MessagesEnum.PARAMETER_NOT_FOUND",
                    f"Parameter not found: {cache_key}"
                )
            self._pda_codes[cache_key] = parameter.prm_string_value
            logger.debug(f"Cached PDA code for {country_iso_code}")

        return self._pda_codes[cache_key]

    def _get_callback_url(self) -> str:
        """Get callback URL from cache or database"""
        if self._callback_url is None:
            parameter = self.parameter_service.get_parameter_by_code(Constants.CALLBACK_URL_EME)
            if not parameter:
                raise BrokerException(
                    "MessagesEnum.PARAMETER_NOT_FOUND",
                    f"Parameter not found: {Constants.CALLBACK_URL_EME}"
                )
            self._callback_url = parameter.prm_string_value
            logger.debug("Cached callback URL")

        return self._callback_url

    @classmethod
    def clear_cache(cls):
        """Clear all cached parameters"""
        cls._agent_logins.clear()
        cls._agency_codes.clear()
        cls._pda_codes.clear()
        cls._callback_url = None
        logger.info("Mapper cache cleared")