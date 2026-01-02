import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.enums import MovementContext, ServiceScope, StatusEnum
from app.schemas.financial.movement import MovementExecutionBO,ResponseDetails,MovementExecutionResponse,MovementExecutionRequest
from app.services.external_call_handler import ExternalCallHandlerService
from app.services.movement import MovementService
from app.services.movement_checker import MovementCheckerService, NoStatusChangingBrokerException, BrokerException
from app.services.engine_entity_loader import EngineEntityLoaderService


logger = logging.getLogger(__name__)


class MovementLoaderService:
    """Service for loading and processing movements"""

    def __init__(self, db: Session):
        self.db = db
        self.logger = logger
        self.engine_entity_loader_service = EngineEntityLoaderService(db)
        self.movement_checker_service = MovementCheckerService(db)
        self.movement_service = MovementService(db)
        self.external_call_handler_service = ExternalCallHandlerService(db)

    # def __init__(
    #         self,
    #         db: Session,
    #         movement_service: MovementService,
    #         movement_checker_service: MovementCheckerService,
    #         engine_entity_loader_service: EngineEntityLoaderService,
    # ):
    #     self.db = db
    #     self.movement_service = movement_service
    #     self.movement_checker_service = movement_checker_service
    #     self.engine_entity_loader_service = engine_entity_loader_service

    def load_movement(self, execution_bo: Dict[str, Any]) -> MovementExecutionBO:
        """
        Load and process a movement

        Args:
            execution_bo: Movement execution business object

        Returns:
            Updated execution_bo

        """
        logger.info("=" * 80)
        logger.info("Starting movement check process")

        if not isinstance(execution_bo, MovementExecutionBO):
            execution_bo = MovementExecutionBO(**execution_bo)
        else:
            execution_bo = execution_bo

        try:
            logger.info("Loading movement...")

            # Check if movement is locally initiated
            if not execution_bo.local_init:
                self.retrieve_movement(execution_bo)
                self.check_if_movement_can_be_loaded(execution_bo)
                self.retrieve_reference_data_before_loading(execution_bo)
            else:
                logger.info("Movement locally initiated. Not retrieving & checking status")

            # Update status to LOADED
            loaded_status = self.engine_entity_loader_service.get_status_by_code(StatusEnum.BK_LOADED.name)
            self.movement_service.update_status(
                execution_bo.movement,
                loaded_status,
                execution_bo.request.user_login,
                ""
            )

            # Check for validation constraints
            # self.movement_checker_service.check_for_constraints(
            #     execution_bo,
            #     MovementContext.VALIDATION
            # )

            # Get validated OTP
            #self.get_valid_otp(execution_bo)

            # Check amount for PI scope
            if execution_bo.service.scope == ServiceScope.PI:
                self.check_amount(execution_bo)

            # Handle external/PI scope services
            if execution_bo.service.scope in [ServiceScope.EXTERNAL, ServiceScope.PI]:
                #pass
                # self.set_partner_dist_id(execution_bo)
                self.external_call_handler_service.handle_external_call(execution_bo)
                #
                if execution_bo.can_create_operations:
                     #self.recompute_charge_and_commission(execution_bo)
                     self.do_post_success_actions(execution_bo)
                elif (execution_bo.response_details and
                       "FAILED" in execution_bo.response_details.status):

                    logger.info(" execution failed with ")
                    # Remove partner dist ID for retry capability
                    # self.remove_partner_dist_id_from_temp(execution_bo.movement)
                    # self.trigger_change_handler_for_failed_movement(
                    #     execution_bo.movement.tag,
                    #     execution_bo.movement.gu_id
                    # )
            else:
                # Internal service - mark as successful
                successful_status = self.engine_entity_loader_service.get_status_by_code(
                    StatusEnum.BK_SUCCESSFUL.name
                )
                self.movement_service.update_status(
                    execution_bo.movement,
                    successful_status,
                    execution_bo.request.user_login,
                    "SUCCESS"
                )
                self.do_post_success_actions(execution_bo)

            # Send notification
            #self.send_movement_to_notification(execution_bo)

            logger.info("Movement loaded successfully")

        except NoStatusChangingBrokerException as e:
            logger.error(f"No status changing error while loading movement: {e}")
            self.movement_checker_service.handle_default_exception(e, execution_bo)
            raise

        except BrokerException as e:
            logger.error(f"Broker error while loading movement: {e}")
            self.handle_broker_exception(e, execution_bo)
            #self.send_movement_to_notification(execution_bo)

        except Exception as e:
            logger.error(f"Unexpected error while loading movement: {e}", exc_info=True)
            self.movement_checker_service .handle_default_exception(e, execution_bo)

        return execution_bo

    def get_valid_otp(self, execution_bo: MovementExecutionBO) -> MovementExecutionBO:
        """
        Validate OTP if required by flow constraints

        Args:
            execution_bo: Movement execution business object

        Returns:
            Updated execution_bo

        Raises:
            BrokerException: If OTP validation fails
        """
        if not execution_bo.flow or not execution_bo.flow.constraints:
            return execution_bo

        for constraint in execution_bo.flow.constraints:
            if constraint.code == ConstraintType.CHECK_ISSUER_OTP:
                # Check if OTP and channel are provided
                if (not execution_bo.request.additional_informations or
                        'totp' not in execution_bo.request.additional_informations or
                        'channel' not in execution_bo.request.additional_informations):
                    raise BrokerException(
                        "OTP code or channel not provided",
                        MessagesEnum.CODE_OTP_OR_CHANNEL_NOT_PROVIDED
                    )

                # Skip validation for DOUBLE_FACTOR channel
                channel = execution_bo.request.additional_informations.get('channel')
                if channel == Channel.DOUBLE_FACTOR.name:
                    logger.info(f"OTP channel is: {Channel.DOUBLE_FACTOR.name}")
                    return execution_bo

                # Validate OTP
                totp_code = execution_bo.request.additional_informations.get('totp')
                otp = self.engine_entity_loader_service.get_otp_by_code_and_guid(
                    totp_code,
                    Channel[channel],
                    execution_bo.request.gu_id
                )

                if not otp or not otp.is_checked or otp.is_used:
                    raise BrokerException(
                        "OTP code not valid",
                        MessagesEnum.CODE_OTP_NOT_VALID
                    )

                # Mark OTP as used
                otp.is_used = True
                self.engine_entity_loader_service.update_otp(otp)
                logger.info(f"OTP validated and marked as used: {totp_code}")

        return execution_bo

    def do_post_success_actions(self, execution_bo: MovementExecutionBO) -> MovementExecutionBO:
        """
        Perform post-success actions after movement is loaded

        Args:
            execution_bo: Movement execution business object

        Returns:
            Updated execution_bo
        """
        logger.info("Executing post-success actions...")

        # Send status change notification
        #self.send_status_change_to_jms(execution_bo)

        # Set success response if not already set
        if (not execution_bo.response_details or
                execution_bo.response_details.status != "SUCCESS"):
            execution_bo.response_details = ResponseDetails(
                code="SUCCESS",
                message="SUCCESS",
                is_error=True
            )
        sucesss = self.engine_entity_loader_service.get_status_by_code(StatusEnum.SUCCESSFUL.name)

        # self.movement_service.update_status(
        #     execution_bo.movement,
        #     sucesss,
        #     execution_bo.request.user_login,
        #     "SUCCESS"
        # )

        self.movement_service.update_status_movement(
            execution_bo.movement.id,
            sucesss,
            execution_bo.request.user_login,
            "SUCCESS",
            execution_bo.movement.gu_id,
            None
        )


        # Refund overdraft if applicable
        #self.refund_overdraft(execution_bo)

        # Notify BET regulator if applicable
        #self.notify_bet_regulator(execution_bo)

        logger.info("Post-success actions completed")
        return execution_bo

    def retrieve_reference_data_before_loading(
            self, execution_bo: MovementExecutionBO
    ) -> MovementExecutionBO:
        """
        Retrieve all reference data needed before loading movement

        Args:
            execution_bo: Movement execution business object

        Returns:
            Updated execution_bo
        """
        logger.info("Retrieving reference data before loading...")

        self.find_service(execution_bo)
        self.find_legal_entity(execution_bo)
        self.find_flow(execution_bo)
        #self.find_service_provider(execution_bo)
        self.find_accounts(execution_bo)
        self.check_for_impact_rules(execution_bo)

        logger.info("Reference data retrieved successfully")
        return execution_bo

    def find_legal_entity(self, execution_bo: MovementExecutionBO) -> None:
        """Retrieve legal entity - delegates to movement checker"""
        self.movement_checker_service.retrieve_legal_entity(execution_bo)

    def find_service(self, execution_bo: MovementExecutionBO) -> None:
        """Retrieve service - delegates to movement checker"""
        self.movement_checker_service.find_service(execution_bo)

    def find_flow(self, execution_bo: MovementExecutionBO) -> None:
        """Retrieve flow - delegates to movement checker"""
        execution_bo.flow = self.engine_entity_loader_service.get_flow_by_code(execution_bo.movement.flow_code)

    def find_service_provider(self, execution_bo: MovementExecutionBO) -> None:
        """Retrieve service provider - delegates to movement checker"""
        self.movement_checker_service.find_service_provider(execution_bo)

    def find_accounts(self, execution_bo: MovementExecutionBO) -> None:
        """Retrieve accounts - delegates to movement checker"""
        self.movement_checker_service.find_accounts(execution_bo)

    def check_for_impact_rules(self, execution_bo: MovementExecutionBO) -> None:
        """Check impact rules - delegates to movement checker"""
        self.movement_checker_service.check_for_impact_rules(execution_bo, save_operations=False)

    def retrieve_movement(self, execution_bo: MovementExecutionBO) -> None:
        """
        Retrieve existing movement from database

        Args:
            execution_bo: Movement execution business object
        """
        logger.info(f"Retrieving movement with GUID: {execution_bo.request.gu_id}")

        movement = self.movement_service.find_by_guid(execution_bo.request.gu_id)
        if not movement:
            raise BrokerException(
                f"Movement not found: {execution_bo.request.gu_id}",
                "MOVEMENT_NOT_FOUND"
            )

        execution_bo.movement = movement
        logger.info(f"Movement retrieved: {movement.id}")

    def check_if_movement_can_be_loaded(self, execution_bo: MovementExecutionBO) -> None:
        """
        Check if movement status allows loading

        Args:
            execution_bo: Movement execution business object

        Raises:
            BrokerException: If movement cannot be loaded
        """
        if not execution_bo.movement:
            raise BrokerException("Movement not found", "MOVEMENT_NOT_FOUND")

        allowed_statuses = [StatusEnum.BK_INITIATED.name, StatusEnum.BK_LOADED.name]
        if execution_bo.movement.status_code not in allowed_statuses:
            raise BrokerException(
                f"Movement cannot be loaded from status: {execution_bo.movement.status_code}",
                "INVALID_MOVEMENT_STATUS",
                execution_bo.movement.status_code
            )

        logger.info(f"Movement can be loaded. Current status: {execution_bo.movement.status_code}")

    def check_amount(self, execution_bo: MovementExecutionBO) -> None:
        """Check amount validity for PI scope services"""
        # Implement amount validation logic based on your business rules
        logger.info(f"Checking amount: {execution_bo.request.amount}")
        pass

    def set_partner_dist_id(self, execution_bo: MovementExecutionBO) -> None:
        """Set or validate partner distribution ID"""
        logger.info("Setting partner distribution ID...")
        self.partner_dist_id_temp_service.set_partner_dist_id(execution_bo)

    def recompute_charge_and_commission(self, execution_bo: MovementExecutionBO) -> None:
        """Recompute charges and commissions after external call"""
        logger.info("Recomputing charges and commissions...")
        # Implement recomputation logic based on external response
        pass

    # def remove_partner_dist_id_from_temp(self, movement: Movement) -> None:
    #     """Remove partner dist ID from temporary storage for retry"""
    #     if movement.partner_dist_id:
    #         self.partner_dist_id_temp_service.remove(movement.partner_dist_id)
    #         logger.info(f"Removed partner dist ID: {movement.partner_dist_id}")
    #
    # def trigger_change_handler_for_failed_movement(self, tag: str, gu_id: str) -> None:
    #     """Trigger change handler for failed movement"""
    #     if tag:
    #         logger.info(f"Triggering change handler for failed movement: {gu_id}")
    #         self.change_handler_service.handle_failed_movement(tag, gu_id)
    #
    # def send_status_change_to_jms(self, execution_bo: MovementExecutionBO) -> None:
    #     """Send status change notification to JMS queue"""
    #     logger.info("Sending status change to JMS...")
    #     # Implement JMS notification logic
    #     pass
    #
    # def refund_overdraft(self, execution_bo: MovementExecutionBO) -> None:
    #     """Refund overdraft if applicable"""
    #     if execution_bo.overdraft_issued:
    #         logger.info("Refunding overdraft...")
    #         self.credit_digital_service.refund_overdraft(execution_bo)
    #
    # def notify_bet_regulator(self, execution_bo: MovementExecutionBO) -> None:
    #     """Notify BET regulator if applicable"""
    #     if self.should_notify_bet_regulator(execution_bo):
    #         logger.info("Notifying BET regulator...")
    #         self.bet_regulator_notification_service.notify(execution_bo)
    #
    # def should_notify_bet_regulator(self, execution_bo: MovementExecutionBO) -> bool:
    #     """Check if BET regulator should be notified"""
    #     # Implement logic to determine if notification is needed
    #     return False
    #
    # def send_movement_to_notification(self, execution_bo: MovementExecutionBO) -> None:
    #     """Send movement to notification service"""
    #     logger.info("Sending movement to notification service...")
    #     self.notification_service.send_notification(execution_bo)

    def handle_broker_exception(
            self, exception: BrokerException, execution_bo: MovementExecutionBO
    ) -> None:
        """Handle broker exception"""
        logger.error(f"Handling broker exception: {exception}")

        # Update movement status to failed
        if execution_bo.movement:
            failed_status = self.engine_entity_loader_service.get_status_by_code(
                StatusEnum.BK_FAILED.name
            )
            self.movement_service.update_status(
                execution_bo.movement,
                failed_status,
                execution_bo.request.user_login if execution_bo.request else None,
                str(exception)
            )

        # Set error response
        execution_bo.response_details = ResponseDetails(
            code=exception.code or "FAILED",
            is_error=True,
            message=str(exception)
        )

    def handle_no_status_changing_broker_exception(
            self, exception: NoStatusChangingBrokerException, execution_bo: MovementExecutionBO
    ) -> None:
        """Handle no status changing broker exception"""
        logger.error(f"Handling no status changing exception: {exception}")

        # Set error response without changing status
        execution_bo.response_details = ResponseDetails(
            code=exception.code or "FAILED",
            is_error=True,
            message=str(exception)
        )
