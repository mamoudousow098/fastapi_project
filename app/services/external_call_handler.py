"""
External call handler service - FastAPI equivalent of Java ExternalCallHandlerServiceBean
"""
import logging
import json
import re
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import httpx

from app.models.enums import StatusEnum
from app.models.movement import Movement
from app.models.parameter import Parameter
from app.models.service_mapping import ServiceMapping
from app.models.enums import  ServiceScope, Gateway
from app.models.provider import Provider
from app.schemas.financial.movement import MovementExecutionResponse, ResponseDetails, MovementExecutionBO
from app.schemas.mappers.map_transaction_exchange import MapTransactionExchangeToMovementRequest
from app.schemas.transaction_exchange import TransactionExchange
from app.services.movement import MovementService
from app.services.engine_entity_loader import EngineEntityLoaderService
from app.services.parameter import ParameterService
from app.services.service_mapping import ServiceMappingService
from app.services.movement_checker import BrokerException, NoStatusChangingBrokerException
from app.utils.http_utils import  HTTPResponse
from app.utils.broker_gateway import   BrokerGateway

#from app.utils.mappers import MapTransactionExchangeToMovementRequest

logger = logging.getLogger(__name__)

PROJECT_TOPIC_PATTERN = re.compile(r'^[^:\s]+:[^:\s]+$')


class ExternalCallHandlerService:
    """Service for handling external partner calls"""

    def __init__(self, db: Session):
        self.db = db
        self.movement_service = MovementService(db)
        self.engine_entity_loader_service = EngineEntityLoaderService(db)
        self.service_mapping_service = ServiceMappingService(db)
        # ✅ CORRECT: Initialize mapper with db session
        self.mapper = MapTransactionExchangeToMovementRequest(db)

        self.broker_gateway = BrokerGateway(db)

    def handle_external_call(self, execution_bo: MovementExecutionBO) -> object:
        """
        Handle an external call, involving mapping the request to a transaction exchange,
        calling the external service, mapping the response to a broker response, and
        updating the movement status based on the response.

        Args:
            execution_bo: MovementExecutionBO - the movement execution business object

        Returns:
            Updated MovementExecutionBO

        Raises:
            BrokerException: if there is an error while calling the external service
            NoStatusChangingBrokerException: if the movement status cannot be changed
        """
        logger.info("=" * 80)
        logger.info("Starting external call handling process")
        logger.info(f"Movement GUID: {execution_bo.request.gu_id}")
        logger.info("=" * 80)

        try:
            # Step 1: Find service URL
            self.find_service_url_for_external_call(execution_bo)

            # Step 2: Map request to transaction exchange
            self.map_request_to_transaction_exchange(execution_bo)

            # Step 3: Update movement status before calling
            self.update_movement_status_before_calling_external_partner(execution_bo)

            # Step 4: Call external service
            self.call_external_service(execution_bo)

            # Step 5: Map response and update status
            self.map_external_call_response_and_update_movement_status(execution_bo)

            # Step 6: Map to broker response
            self.map_external_call_response_to_broker_response(execution_bo)

            logger.info("External call handling completed successfully")
            return execution_bo

        except Exception as e:
            logger.error(f"Error during external call handling: {str(e)}", exc_info=True)
            raise


    def find_service_url_for_external_call(self, execution_bo: MovementExecutionBO) -> object:
        """
        Find the service URL to call for the given MovementExecutionBO.

        Priority:
        1. ServiceProvider URL (if set)
        2. Parameter by service code
        3. Throw exception if not found

        Args:
            execution_bo: MovementExecutionBO

        Returns:
            Updated MovementExecutionBO with partner_url_parameter set

        Raises:
            BrokerException: if service URL is not found
        """
        logger.info("Finding service URL for external call")

        # Check if ServiceProvider has a URL
        if (execution_bo.service_provider and
                execution_bo.service_provider.url and
                execution_bo.service_provider.url.strip()):

            url = execution_bo.service_provider.url
            is_localhost = "localhost" in url

            execution_bo.partner_url_parameter = Parameter(
                prm_string_value=url,
                prm_value=0 if is_localhost else 1
            )
            logger.info(f"Using ServiceProvider URL: {url}")

            # ✅ Return early after setting URL from ServiceProvider
            return execution_bo

        else :
            logger.info(" service provider is null  " + str(execution_bo.service_provider) + " url " + str(execution_bo.service_provider.url) )

        # Check if service code is set
        if execution_bo.movement.service_code:
            parameter = self.engine_entity_loader_service.get_parameter_by_code(
                execution_bo.movement.service_code
            )

            if parameter:
                execution_bo.partner_url_parameter = parameter
                logger.info(f"Using parameter URL for service: {execution_bo.movement.service_code}")

                # ✅ Return early after setting URL from parameter
                return execution_bo
            else:
                logger.info(f"Won't call partner for transaction :: {execution_bo.request.gu_id}")
                raise BrokerException(
                    MessagesEnum.SERVICE_URL_NOT_FOUND,
                    f"Service URL not found for service code: {execution_bo.movement.service_code}"
                )
        else:
            logger.info(f"Service code is null. Won't call partner for transaction :: {execution_bo.request.gu_id}")

        # ✅ Validate PubSub format AFTER setting partner_url_parameter
        # This check happens only if we reach here (after parameter is set)
        if (execution_bo.service_provider and
                execution_bo.service_provider.gateway == Gateway.PUB_SUB and
                execution_bo.partner_url_parameter and
                not self._is_valid_project_topic(execution_bo.partner_url_parameter.prm_string_value)):

            logger.error(f"Invalid project:topic format: {execution_bo.partner_url_parameter.prm_string_value}")
            raise BrokerException(
                MessagesEnum.INVALID_PROJECT_TOPIC_FORMAT,
                f"Invalid project:topic format for PubSub gateway"
            )

        return execution_bo

    # def find_service_url_for_external_call(self, execution_bo) -> object:
    #     """
    #     Find the service URL to call for the given MovementExecutionBO.
    #
    #     Priority:
    #     1. ServiceProvider URL (if set)
    #     2. Parameter by service code
    #     3. Throw exception if not found
    #
    #     Args:
    #         execution_bo: MovementExecutionBO
    #
    #     Returns:
    #         Updated MovementExecutionBO with partner_url_parameter set
    #
    #     Raises:
    #         BrokerException: if service URL is not found
    #     """
    #     logger.info("Finding service URL for external call")
    #
    #     # Check if ServiceProvider has a URL
    #     if (execution_bo.service_provider and
    #             execution_bo.service_provider.url and
    #             execution_bo.service_provider.url.strip()):
    #
    #         url = execution_bo.service_provider.url
    #         is_localhost = "localhost" in url
    #
    #         execution_bo.partner_url_parameter = Parameter(
    #             prm_string_value=url,
    #             prm_value=0 if is_localhost else 1
    #         )
    #         logger.info(f"Using ServiceProvider URL: {url}")
    #
    #         # Validate PubSub format if needed
    #         if (execution_bo.service_provider.gateway == Gateway.PUB_SUB and
    #                 not self._is_valid_project_topic(url)):
    #             logger.error(f"Invalid project:topic format: {url}")
    #             raise BrokerException(
    #                 "MessagesEnum.INVALID_PROJECT_TOPIC_FORMAT",
    #                 "Invalid project:topic format for PubSub gateway"
    #             )
    #
    #         return execution_bo
    #
    #     # Check if service code is set
    #     if execution_bo.movement.service_code:
    #         parameter = self.engine_entity_loader_service.get_parameter_by_code(
    #             execution_bo.movement.service_code
    #         )
    #
    #         if parameter:
    #             execution_bo.partner_url_parameter = parameter
    #             logger.info(f"Using parameter URL for service: {execution_bo.movement.service_code}")
    #
    #             # Validate PubSub format if needed
    #             if (execution_bo.service_provider and
    #                     execution_bo.service_provider.gateway == Gateway.PUB_SUB and
    #                     not self._is_valid_project_topic(parameter.prm_string_value)):
    #                 logger.error(f"Invalid project:topic format: {parameter.prm_string_value}")
    #                 raise BrokerException(
    #                     "MessagesEnum.INVALID_PROJECT_TOPIC_FORMAT",
    #                     "Invalid project:topic format for PubSub gateway"
    #                 )
    #
    #             return execution_bo
    #         else:
    #             logger.error(f"Service URL not found for: {execution_bo.movement.service_code}")
    #             raise BrokerException(
    #                 "MessagesEnum.SERVICE_URL_NOT_FOUND",
    #                 f"Service URL not found for service code: {execution_bo.movement.service_code}"
    #             )
    #     else:
    #         logger.info(f"Service code is null. Won't call partner for transaction: {execution_bo.request.gu_id}")
    #
    #     return execution_bo

    @staticmethod
    def _is_valid_project_topic(input_str: Optional[str]) -> bool:
        """Validate project:topic format for PubSub"""
        if not input_str:
            return False
        return bool(PROJECT_TOPIC_PATTERN.match(input_str))

    def map_request_to_transaction_exchange(self, execution_bo) -> object:
        """
        Maps a MovementExecutionBO to a TransactionExchange for calling an external partner.

        If the service scope is not EXTERNAL, it simply returns the MovementExecutionBO.

        Args:
            execution_bo: MovementExecutionBO

        Returns:
            Updated MovementExecutionBO with transaction_exchange set

        Raises:
            BrokerException: if ServiceMapping is not found
        """
        logger.info("Mapping request to transaction exchange")

        if execution_bo.service.scope != ServiceScope.EXTERNAL:
            logger.info("Service scope is not EXTERNAL, skipping mapping")
            return execution_bo

        # Get service mapping
        service_mapping = self.service_mapping_service.get_by_code_gu3(
            execution_bo.movement.service_code
        )

        if not service_mapping:
            logger.error(f"No service mapping found for: {execution_bo.movement.service_code}")
            raise BrokerException(
                "NO_MATCHING_EXTERNAL_SERVICE_CODE",
                f"No matching external service code for: {execution_bo.movement.service_code}"
            )

        execution_bo.service_mapping = service_mapping

        # Map to transaction exchange
        transaction_exchange = MapTransactionExchangeToMovementRequest.movement_exchange_to_transaction_exchange(
            execution_bo
        )

        # Set external service code and context
        transaction_exchange.service_exchange.service_code = service_mapping.code_gu1
        transaction_exchange.service_exchange.infos_sup["serviceContext"] = service_mapping.context

        execution_bo.transaction_exchange = transaction_exchange

        logger.info(f"Transaction exchange created with service code: {service_mapping.code_gu1}")
        return execution_bo

    def update_movement_status_before_calling_external_partner(self, execution_bo) -> object:
        """
        Updates the movement status and sets the sent date before calling an external partner.

        Args:
            execution_bo: MovementExecutionBO

        Returns:
            Updated MovementExecutionBO

        Raises:
            NoStatusChangingBrokerException: if the status cannot be changed
        """
        logger.info("Updating movement status to PART_INITIATED")

        # Set sent date
        execution_bo.movement.sent_date = datetime.now()

        # Update status to PART_INITIATED
        part_initiated_status = self.engine_entity_loader_service.get_status_by_code(
            StatusEnum.PART_INITIATED.name
        )

        self.movement_service.update_status(
            execution_bo.movement,
            part_initiated_status,
            execution_bo.movement.user_login,
            "None"
        )

        logger.info("Movement status updated to PART_INITIATED")
        return execution_bo

    def call_external_service(self, execution_bo) -> object:
        """
        Call an external partner.

        Args:
            execution_bo: MovementExecutionBO

        Returns:
            Updated MovementExecutionBO with response details

        Raises:
            BrokerException: if an error occurred while calling the external partner
        """
        logger.info("Calling external service")

        try:
            response: Optional[HTTPResponse] = None

            # Handle different service scopes
            if execution_bo.service.scope == ServiceScope.EXTERNAL:
                provider_gateway = (execution_bo.flow.provider.gateway
                                    if execution_bo.flow.provider else None)

                # USSD Gateway
                if provider_gateway == Gateway.USSD:
                    logger.info("Using USSD gateway")

                    self.mapper.add_additional_infos_for_ussd(
                        execution_bo, execution_bo.transaction_exchange
                    )
                    response = self.broker_gateway.put_to_connector(
                        execution_bo.partner_url_parameter,
                        json.dumps(execution_bo.transaction_exchange.dict()),
                        execution_bo.movement.service_code
                    )

                # CONNECTOR Gateway
                elif provider_gateway == Gateway.CONNECTOR:
                    logger.info("Using CONNECTOR gateway")
                    self.mapper.add_additional_infos_for_connector(
                        execution_bo, execution_bo.transaction_exchange
                    )
                    url_context = MapTransactionExchangeToMovementRequest.get_connector_url_context(
                        execution_bo, execution_bo.transaction_exchange
                    )
                    response = self.broker_gateway.get_to_connector(
                        execution_bo.partner_url_parameter,
                        url_context,
                        execution_bo.movement.service_code
                    )

                # PUB_SUB Gateway
                # elif provider_gateway == Gateway.PUB_SUB:
                #     logger.info("Using PUB_SUB gateway")
                #     MapTransactionExchangeToMovementRequest.add_additional_infos_for_connector(
                #         execution_bo, execution_bo.transaction_exchange
                #     )
                #     message_id = PubSubUtils.send_transaction(
                #         execution_bo.transaction_exchange,
                #         execution_bo.partner_url_parameter.prm_string_value
                #     )
                #     response = HTTPResponse(body=message_id)

                # Default: POST to connector
                else:
                    logger.info("Using default POST gateway")
                    response = self.broker_gateway.post_to_connector(
                        execution_bo.partner_url_parameter,
                        json.dumps(execution_bo.transaction_exchange.dict()),
                        execution_bo.movement.service_code
                    )

            # PI Service Scope
            elif execution_bo.service.scope == ServiceScope.PI:
                logger.info("Calling PI service")
                response = self.broker_gateway.post_to_connector(
                    execution_bo.partner_url_parameter,
                    json.dumps(execution_bo.request.dict()),
                    execution_bo.movement.service_code
                )

            else:
                logger.error(f"Unknown service scope: {execution_bo.service.scope}")
                raise BrokerException(
                    "MessagesEnum.SERVICE_SCOPE_NOT_FOUND",
                    f"Service scope not found: {execution_bo.service.scope}"
                )

            # Process response
            if response:
                self._process_external_response(execution_bo, response)

            logger.info(f"Response details: {execution_bo.response_details}")
            return execution_bo

        except BrokerException:
            raise
        except Exception as e:
            logger.error(f"Error calling external partner: {str(e)}", exc_info=True)
            raise BrokerException(
                "MessagesEnum.EXTERNAL_CALL_ERROR",
                f"Error calling external partner: {str(e)}"
            )

    def _process_external_response(self, execution_bo, response: HTTPResponse):
        """Process the external service response"""

        logger.info(" http code response " + str(response.code))

        # Handle PUB_SUB response
        if (execution_bo.service.scope == ServiceScope.EXTERNAL and
                execution_bo.service_provider.gateway == Gateway.PUB_SUB):
            if response.body:
                execution_bo.response_details = ResponseDetails(
                    status="PART_LOADED",
                    message=f"Message sent to topic with ID: {response.body}",
                    is_async=False
                )
            else:
                execution_bo.response_details = ResponseDetails(
                    status="PART_FAILED",
                    message="Failed to send message to topic",
                    is_async=False
                )
            return

        # Handle EXTERNAL service response
        if execution_bo.service.scope == ServiceScope.EXTERNAL:
            transaction_exchange = None
            try:
                transaction_exchange = TransactionExchange(**json.loads(response.body))
            except Exception as e:
                logger.error(f"Error parsing transaction exchange: {e}")

            if transaction_exchange:
                error_code = transaction_exchange.error_code

                logger.info(" errorCode " + error_code)

                # Success codes
                if error_code in ["200", "600"]:
                    execution_bo.response_details = ResponseDetails(
                        status="PART_SUCCESSFUL",
                        code="PART_SUCCESSFUL",
                        is_error=False
                    )
                # Failure codes
                elif error_code in ["404", "400", "300", "401", "403", "500", "505"] or \
                        response.code in [400, 401, 403, 404, 405]:
                    execution_bo.response_details = ResponseDetails(
                        status="PART_FAILED",
                        is_error=False
                    )
                    execution_bo.response_details.message = transaction_exchange.error_message
                # Pending codes
                else:
                    execution_bo.response_details = ResponseDetails(
                        status="PART_LOADED",
                        is_error=False
                    )
                    execution_bo.response_details.message = transaction_exchange.error_message

                # Process additional information
                if (transaction_exchange.service_exchange and
                        transaction_exchange.service_exchange.infos_sup):

                    infos_sup = transaction_exchange.service_exchange.infos_sup

                    # SMS message handling
                    if (execution_bo.flow.provider.gateway != Gateway.USSD and
                            infos_sup.get("sms")):
                        execution_bo.response_details.message = infos_sup["sms"]

                    # Update additional informations
                    execution_bo.request.additional_informations = infos_sup
                    self._update_movement_add_infos(execution_bo)

                    # Update partner ID
                    execution_bo.movement.partner_id = infos_sup.get("numTransaction")

                    # Update commission base
                    if infos_sup.get("frais"):
                        execution_bo.movement.charge_base = float(infos_sup["frais"])
                        execution_bo.movement.commission_base = float(infos_sup["frais"])
                        execution_bo.recompute_operations = True
                    elif infos_sup.get("baseCalculCommission"):
                        execution_bo.movement.charge_base = float(infos_sup["baseCalculCommission"])
                        execution_bo.movement.commission_base = float(infos_sup["baseCalculCommission"])
                        execution_bo.recompute_operations = True
            else:
                # No transaction exchange parsed
                if response.code in [401, 403, 404, 405]:
                    execution_bo.response_details = ResponseDetails(
                        status="PART_FAILED",
                        is_error=False
                    )
                else:
                    execution_bo.response_details = ResponseDetails(
                        status="PART_LOADED",
                        is_error=False
                    )

            # Handle server errors
            if response.code >= 500:
                execution_bo.response_details = ResponseDetails(
                    status="PART_LOADED",
                    is_error=False
                )

        # Handle PI service response
        elif execution_bo.service.scope == ServiceScope.PI:
            if 300 < response.code < 500:
                try:
                    response_body = MovementExecutionResponse(**json.loads(response.body))
                    if response_body and response_body.response_details:
                        execution_bo.response_details = response_body.response_details
                    else:
                        execution_bo.response_details = ResponseDetails(
                            status="PART_FAILED",
                            is_error=False
                        )
                except Exception:
                    execution_bo.response_details = ResponseDetails(
                        status="PART_FAILED",
                        is_async=False
                    )
            elif response.code >= 500:
                execution_bo.response_details = ResponseDetails(
                    status="PART_LOADED",
                    is_async=False
                )
            else:
                response_body = MovementExecutionResponse(**json.loads(response.body))
                if response_body:
                    execution_bo.response_details = response_body.response_details

    def map_external_call_response_and_update_movement_status(self, execution_bo) -> object:
        """
        Update the movement status based on the partner call response.
        If there isn't any partner call, the movement will go directly to PART_SUCCESSFUL

        Args:
            execution_bo: MovementExecutionBO

        Returns:
            Updated MovementExecutionBO

        Raises:
            NoStatusChangingBrokerException: if status cannot be changed
        """
        logger.info("Mapping external call response and updating movement status")

        if not execution_bo.response_details:
            logger.warning(f"No response details for movement: {execution_bo.response.gu_id}")
            status = self.engine_entity_loader_service.get_status_by_code(
                StatusEnum.PART_LOADED.name
            )
            self.movement_service.update_status(
                execution_bo.movement,
                status,
                execution_bo.movement.user_login,
                "No message found"
            )

        elif execution_bo.response_details.status == StatusEnum.PART_SUCCESSFUL.name:
            status = self.engine_entity_loader_service.get_status_by_code(
                StatusEnum.PART_SUCCESSFUL.name
            )
            self.movement_service.update_status(
                execution_bo.movement,
                status,
                execution_bo.movement.user_login,
                "SUCCESS"
            )
            execution_bo.can_create_operations = True

        elif execution_bo.response_details.status == StatusEnum.PART_FAILED.name:
            status = self.engine_entity_loader_service.get_status_by_code(
                StatusEnum.PART_FAILED.name
            )
            self.movement_service.update_status(
                execution_bo.movement,
                status,
                execution_bo.movement.user_login,
                execution_bo.response_details.message
            )

        else:
            status = self.engine_entity_loader_service.get_status_by_code(
                StatusEnum.PART_LOADED.name
            )
            self.movement_service.update_status(
                execution_bo.movement,
                status,
                execution_bo.movement.user_login,
                execution_bo.response_details.message
            )

        logger.info(
            f"Status set to {execution_bo.response_details.status if execution_bo.response_details else None} "
            f"for movement {execution_bo.movement.gu_id}"
        )

        return execution_bo

    def map_external_call_response_to_broker_response(self, execution_bo) -> object:
        """
        Map the partner call response to a broker response

        Args:
            execution_bo: MovementExecutionBO

        Returns:
            Updated MovementExecutionBO with broker response
        """
        logger.info("Mapping external call response to broker response")

        if not execution_bo.response_details:
            execution_bo.response_details = ResponseDetails(
                status="PENDING",
                message="PENDING",
                is_async=True
            )

        elif execution_bo.response_details.status == StatusEnum.PART_SUCCESSFUL.name:
            execution_bo.response_details = ResponseDetails(
                status="SUCCESS",
                is_async=True
            )

        elif execution_bo.response_details.status == StatusEnum.PART_FAILED.name:
            execution_bo.response_details.status = MessagesEnum.FAILED.name

            if execution_bo.service.scope == ServiceScope.PI:
                # Keep existing errors
                pass
            else:
                execution_bo.response_details.errors = [execution_bo.movement.message]

        else:
            execution_bo.response_details = ResponseDetails(
                status="PENDING",
                message=execution_bo.response_details.message,
                is_async=True
            )

        logger.info(f"Broker response mapped: {execution_bo.response_details.status}")
        return execution_bo

    def _update_movement_add_infos(self, execution_bo):
        """Update movement additional informations from request"""
        if execution_bo.movement and execution_bo.movement.additional_informations:
            if (execution_bo.request and
                    execution_bo.request.additional_informations):
                for key, value in execution_bo.request.additional_informations.items():
                    execution_bo.movement.additional_informations[key] = value
        else:
            if execution_bo.movement and execution_bo.request:
                execution_bo.movement.additional_informations = \
                    execution_bo.request.additional_informations