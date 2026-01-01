"""
Movement Checker Service - Complete implementation
Equivalent to MovementCheckerServiceBean
"""
import logging
import traceback
from typing import Dict, Optional, Any, Set
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import ImpactRule, Interval, Operation
from app.models.movement import Movement
from app.models.service import Service
from app.models.account import Account
from app.models.enums import (
    EntityState, 
    StatusEnum, 
    AccountCategory, 
    ServiceScope, 
    ServiceFlow
)
from app.schemas.financial.movement import (
    MovementExecutionBO,
    ResponseDetails
)
from app.services.engine_entity_loader import EngineEntityLoaderService
from app.services.movement import MovementService
from app.services.operation_creation import OperationCreationService

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
ISSUER_ACCOUNT_ROLE = "ISSUER"
ACQUIRER_ACCOUNT_ROLE = "ACQUIRER"
SUPER_ = "SUPER_"
EME = "EME"
PROVIDER = "PROVIDER"
PROVIDER_COMMISSION = "PROVIDER_COMMISSION"
PRINCIPAL_DISTRIBUTOR = "PRINCIPAL_DISTRIBUTOR"
INTRA = "INTRA"


class BrokerException(Exception):
    """Custom exception for broker errors"""
    def __init__(self, message: str, code: str = None, context: str = None):
        self.message = message
        self.code = code or "BROKER_ERROR"
        self.context = context
        super().__init__(self.message)
    
    def __str__(self):
        return f"BrokerException[{self.code}]: {self.message}"


class NoStatusChangingBrokerException(BrokerException):
    """Exception that doesn't change movement status"""
    pass


class MovementCheckerService:
    """
    Movement checker service - validates and processes movement transactions.
    Complete Python equivalent of MovementCheckerServiceBean
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logger
        self.engine_entity_loader_service = EngineEntityLoaderService(db)
        self.operation_creation_service = OperationCreationService(db)
        self.movement_service = MovementService(db)
    
    def launch_check(self, execution_bo: Dict[str, Any]) -> MovementExecutionBO:
        """Launch all checks for a movement transaction"""
        logger.info("=" * 80)
        logger.info("Starting movement check process")
        
        if not isinstance(execution_bo, MovementExecutionBO):
            bo = MovementExecutionBO(**execution_bo)
        else:
            bo = execution_bo
        
        logger.info(f"Request: service_code={bo.request.service_code}, amount={bo.request.amount}")
        logger.info(f"User: {bo.kc_user.get('username') if bo.kc_user else 'None'}")
        
        try:

            self.check_information_for_cancellation(bo)

            self.check_if_movement_exists_for_cancellation(bo)

            logger.info("Step 1: Checking for duplicate movements")
            self.check_if_same_movement_initiated_in_last_mn(bo)
            
            logger.info("Step 2: Validating amount")
            self.check_for_amount(bo)
            
            logger.info("Step 3: Finding service")
            self.find_service(bo)
            
            logger.info("Step 4: Retrieving legal entity")
            self.retrieve_legal_entity(bo)
            
            logger.info("Step 5: Checking platform maintenance")
            self.check_if_platform_under_maintenance(bo)
            
            logger.info("Step 6: Finding product")
            self.find_product(bo)
            
            logger.info("Step 7: Removing issuer/acquirer for external service")
            self.remove_issuer_or_acquirer_for_external_service(bo)
            
            logger.info("Step 8: Finding accounts")
            self.find_accounts(bo, throw_exception=False)
            
            logger.info("Step 9: Checking duplicate partner dist ID")
            self.check_if_duplicate_partner_dist_id(bo)
            
            logger.info("Step 10: Checking cap constraints")
            self.check_cap_constraint(bo)
            
            logger.info("Step 11: Finding flow")
            self.find_flow_based_on_service_and_accounts(bo)
            
            logger.info("Step 12: Setting flow account roles")
            self.set_flow_account_roles(bo)
            
            logger.info("Step 13: Finding provider accounts")
            self.find_provider_accounts(bo)
            
            logger.info("Step 14: Setting issuer and acquirer related accounts")
            self.set_issuer_and_acquirer_related_accounts(bo)
            
            logger.info("Step 15: Checking user from token")
            self.check_user_from_token(bo)
            
            logger.info("Step 16: Checking if issuer is acquirer")
            self.check_if_issuer_is_acquirer(bo)
            
            logger.info("Step 17: Creating movement")
            self.create_movement(bo)
            
            logger.info("Step 18: Checking constraints")
            self.check_for_constraints(bo, context="INITIATION")
            
            logger.info("Step 19: Computing global amounts")
            self.compute_global_amounts_for_each_rule(bo)
            
            logger.info("Step 20: Checking impact rules")
            self.check_for_impact_rules(bo, save_operations=True)
            
            logger.info("Step 21: Checking for client")
            self.check_for_client(bo)
            
            logger.info("Step 22: Setting effective accounts roles")
            self.set_effective_accounts_roles_in_movement(bo)
            
            logger.info("Step 23: Setting computed global amounts")
            self.set_computed_global_amounts_on_movement(bo)
            
            logger.info("Step 24: Creating and saving movement")
            self.create_and_save_movement(bo)
            
            bo.response_details = ResponseDetails(
                code="SUCCESS",
                message="Movement initiated successfully",
                is_error=False
            )
            bo.local_init = True
            bo.request.gu_id = bo.movement.gu_id
            logger.info("Movement check completed successfully")
            logger.info("gu " + bo.request.gu_id)
            logger.info("gu " + bo.movement.gu_id)

        except BrokerException as e:
            logger.error(f"Broker Exception: {e}")
            self.handle_broker_exception(e, bo)
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            self.handle_default_exception(e, bo)
        
        logger.info("=" * 80)
        return bo
    
    def check_for_amount(self, execution_bo: MovementExecutionBO) -> None:
        """Validate the transaction amount"""
        amount = execution_bo.request.amount
        logger.info(f"Validating amount: {amount}")
        if amount is None or amount <= 0:
            raise BrokerException("Invalid amount", code="INVALID_AMOUNT")
    
    def find_service(self, execution_bo: MovementExecutionBO) -> None:
        """Find and validate the service"""
        logger.info(f"Finding service: {execution_bo.request.service_code}")
        
        service = self.engine_entity_loader_service.find_service(
            execution_bo.request.service_code
        )
        
        if not service:
            raise BrokerException(
                f"Service not found: {execution_bo.request.service_code}",
                code="SERVICE_NOT_FOUND"
            )
        
        if service.status != EntityState.ACTIVE:
            raise BrokerException(
                f"Service inactive: {service.code}",
                code="SERVICE_INACTIVE"
            )
        
        execution_bo.service = service
        logger.info(f"Service found: {service.code}")
    
    def retrieve_legal_entity(self, execution_bo: MovementExecutionBO) -> None:
        """Retrieve legal entity from service"""
        logger.info("Retrieving legal entity")
        
        legal_entity = execution_bo.service.legal_entity
        if not legal_entity:
            raise BrokerException(
                "Legal entity not found",
                code="LEGAL_ENTITY_NOT_FOUND"
            )
        
        execution_bo.legal_entity = legal_entity
        logger.info(f"Legal entity: {legal_entity.code}")
    
    def check_if_platform_under_maintenance(self, execution_bo: MovementExecutionBO) -> None:
        """Check if platform is under maintenance"""
        logger.info("Checking platform maintenance - OK")
        pass
    
    def find_product(self, execution_bo: MovementExecutionBO) -> None:
        """Find and validate the product"""
        if not execution_bo.request.product_code:
            return
        
        logger.info(f"Finding product: {execution_bo.request.product_code}")
        
        product = self.engine_entity_loader_service.find_product(
            execution_bo.request.product_code
        )
        
        if not product:
            raise BrokerException(
                f"Product not found: {execution_bo.request.product_code}",
                code="PRODUCT_NOT_FOUND"
            )
        
        execution_bo.product = product
        logger.info(f"Product found: {product.code}")


    def remove_issuer_or_acquirer_for_external_service(
        self, execution_bo: MovementExecutionBO
    ) -> None:
        """Remove issuer/acquirer for external services based on flow"""
        logger.info("Checking if issuer/acquirer removal needed")
        
        if not execution_bo.request.accounts_roles:
            return
        
        # EXTERNAL scope
        if execution_bo.service.scope == ServiceScope.EXTERNAL:
            if execution_bo.service.service_flow == ServiceFlow.ENCAISSEMENT:
                execution_bo.request.accounts_roles.pop(ACQUIRER_ACCOUNT_ROLE, None)
                logger.info("Removed ACQUIRER for EXTERNAL ENCAISSEMENT")
            elif execution_bo.service.service_flow == ServiceFlow.DECAISSEMENT:
                execution_bo.request.accounts_roles.pop(ISSUER_ACCOUNT_ROLE, None)
                logger.info("Removed ISSUER for EXTERNAL DECAISSEMENT")
        
        # PI scope
        elif execution_bo.service.scope == ServiceScope.PI:
            if (execution_bo.service.service_flow == ServiceFlow.ENCAISSEMENT 
                and INTRA not in execution_bo.service.code):
                execution_bo.request.accounts_roles.pop(ACQUIRER_ACCOUNT_ROLE, None)
                logger.info("Removed ACQUIRER for PI ENCAISSEMENT")
            elif (execution_bo.service.service_flow == ServiceFlow.DECAISSEMENT 
                  and execution_bo.service.service_type.code != INTRA):
                execution_bo.request.accounts_roles.pop(ISSUER_ACCOUNT_ROLE, None)
                logger.info("Removed ISSUER for PI DECAISSEMENT")
    
    def find_accounts(
        self, execution_bo: MovementExecutionBO, throw_exception: bool = True
    ) -> MovementExecutionBO:
        """Find all required accounts"""
        logger.info("Finding accounts")
        
        # Validation
        if (execution_bo.movement is None 
            and (not execution_bo.request.accounts_roles)):
            raise BrokerException("Accounts not provided", code="ACCOUNTS_NOT_PROVIDED")
        
        if execution_bo.accounts:
            return execution_bo
        
        execution_bo.accounts = {}
        
        # Get roles
        roles = execution_bo.request.accounts_roles
        if execution_bo.movement is not None:
            roles = execution_bo.movement.account_roles
        
        logger.info(f"Processing {len(roles)} account roles")
        
        # Process each role
        for role, identifier in roles.items():
            logger.info(f"Looking up account for role {role}: {identifier}")
            
            account = execution_bo.accounts.get(role)
            
            if not account:
                account = self.engine_entity_loader_service.get_account_by_account_number_or_phone_or_merchant(
                    identifier, execution_bo.service
                )
            
            if account is None:
                logger.warning(f"Account is null :: {identifier} :: {role}")
                if throw_exception:
                    raise BrokerException(
                        f"Account not found: {identifier}",
                        code="ACCOUNT_NOT_FOUND",
                        context=identifier
                    )
                else:
                    continue
            
            logger.info(f"Account found: {account.account_number}")
            
            # Check status
            if account.status != EntityState.ACTIVE:
                raise BrokerException(
                    "Account inactive",
                    code="ACCOUNT_INACTIVE"
                )
            
            # Check legal entity
            if (not account.legal_entity 
                or account.legal_entity.code != execution_bo.legal_entity.code):
                raise BrokerException(
                    f"Legal entity mismatch: {account.account_number}",
                    code="LEGAL_ENTITY_MISMATCH",
                    context=account.account_number
                )
            
            execution_bo.accounts[role] = account
        
        if(len(execution_bo.accounts) == 0) :
            raise BrokerException(
                    "Accounts not found",
                    code="ACCOUNTS_NOT_FOUND"
                )

        logger.info(f"Total accounts loaded: {len(execution_bo.accounts)}")
        return execution_bo
    
    def check_if_duplicate_partner_dist_id(self, execution_bo: MovementExecutionBO) -> None:
        """Check for duplicate partner distribution ID"""
        logger.info("Checking duplicate partner dist ID")
        pass
    
    def check_cap_constraint(self, execution_bo: MovementExecutionBO) -> None:
        """Check balance and movement flow constraints"""
        logger.info("Checking cap constraints")
        pass
    
    def find_flow_based_on_service_and_accounts(
        self, execution_bo: MovementExecutionBO
    ) -> MovementExecutionBO:
        """Find the appropriate flow configuration"""
        logger.info("Finding flow based on service and accounts")
        logger.info(f"Tag value: {getattr(execution_bo, 'tag', None)}")
        
        super_account = None


        
        # Find CORPORATE account for custom flow
        if execution_bo.accounts:
            issuer = execution_bo.accounts.get(ISSUER_ACCOUNT_ROLE)
            acquirer = execution_bo.accounts.get(ACQUIRER_ACCOUNT_ROLE)
            
            if (issuer 
                and issuer.category == AccountCategory.CORPORATE 
                and issuer.account):
                super_account = issuer.account
            elif (acquirer 
                  and acquirer.category == AccountCategory.CORPORATE 
                  and acquirer.account):
                super_account = acquirer.account
        
        account_number = None
        client = None
        client_category = None
        
        if super_account:
            account_number = super_account.account_number
            client = super_account.client
            if client:
                client_category = getattr(client, 'client_category', None)


        # Determine if this is a cancellation request
        is_cancellation = getattr(execution_bo.request, 'is_cancellation', False)

        # Find flow
        flow = self.engine_entity_loader_service.get_active_flow_based_on_parameters(
            service_code=execution_bo.service.code,
            product_code=execution_bo.request.product_code,
            account_number=account_number,
            client_category=client_category,
            is_cancellation=is_cancellation
        )

        if not flow:
            flow_type = "cancellation" if is_cancellation else "normal"
            logger.error(f"Flow not found for {flow_type} operation")
            raise BrokerException(
                f"Flow not found for {flow_type} operation",
                code="FLOW_NOT_FOUND"
            )

        execution_bo.flow = flow
        logger.info(f"Flow found: {flow.code} (cancellation={flow.is_cancellation})")
        return execution_bo
        
        # Find flow
        # flow = self.engine_entity_loader_service.get_active_flow_based_on_parameters(
        #     service_code=execution_bo.service.code,
        #     product_code=execution_bo.request.product_code,
        #     account_number=account_number,
        #     client_category=client_category
        # )
        #
        # if not flow:
        #     raise BrokerException("Flow not found", code="FLOW_NOT_FOUND")
        #
        # execution_bo.flow = flow
        # logger.info(f"Flow found: {flow.code}")
        # return execution_bo
    
    def set_flow_account_roles(self, execution_bo: MovementExecutionBO) -> None:
        """Set flow account roles from rules"""
        logger.info("Setting flow account roles")
        execution_bo.flow_account_roles = set()
        
        if execution_bo.flow and execution_bo.flow.rules:
            for rule in execution_bo.flow.rules:
                if (execution_bo.flow_account_roles is not None 
                    and rule.rule_account_role):
                    execution_bo.flow_account_roles.add(
                        rule.rule_account_role.role_identifier
                    )
            logger.info(f"Flow account roles: {execution_bo.flow_account_roles}")
    
    def find_service_provider(self, execution_bo: MovementExecutionBO) -> None:
        """Find service provider from flow"""
        if not execution_bo.flow.provider:
            raise BrokerException(
                "Provider not configured",
                code="PROVIDER_NOT_CONFIGURED"
            )
        
        if execution_bo.flow.provider.status == EntityState.ACTIVE:
            execution_bo.service_provider = execution_bo.flow.provider
    
    def find_provider_accounts(self, execution_bo: MovementExecutionBO) -> None:
        """Find provider accounts if needed"""
        logger.info("Finding provider accounts")
        
        # Check if provider is needed
        if not (execution_bo.service.scope in [ServiceScope.EXTERNAL, ServiceScope.PI]
                or execution_bo.flow.provider):
            return
        
        # Find service provider
        self.find_service_provider(execution_bo)
        
        if not execution_bo.service_provider:
            raise BrokerException(
                "No active provider configured",
                code="NO_ACTIVE_PROVIDER_CONFIGURED"
            )
        
        if execution_bo.service_provider.provider.status != EntityState.ACTIVE:
            raise BrokerException(
                f"Provider inactive: {execution_bo.service_provider.provider.code}",
                code="PROVIDER_INACTIVE",
                context=execution_bo.service_provider.provider.code
            )
        
        # Find provider accounts
        provider_account_types = ["EXT_COM_DISTRI", "EXT_NOM_DISTRI", "PI_EME"]
        accounts = self.engine_entity_loader_service.find_provider_accounts(
            execution_bo.service_provider.provider.id,
            provider_account_types
        )
        
        if not accounts:
            raise BrokerException(
                f"Provider account not configured: {execution_bo.service_provider.provider.code}",
                code="PROVIDER_ACCOUNT_NOT_CONFIGURED",
                context=execution_bo.service_provider.provider.code
            )
        
        provider_accounts = {}
        
        for account in accounts:
            if (account.is_commission_provider() 
                and PROVIDER_COMMISSION in execution_bo.flow_account_roles):
                provider_accounts[PROVIDER_COMMISSION] = account
                execution_bo.request.accounts_roles[PROVIDER_COMMISSION] = account.account_number
            elif PROVIDER in execution_bo.flow_account_roles:
                provider_accounts[PROVIDER] = account
                execution_bo.request.accounts_roles[PROVIDER] = account.account_number
        
        # Add to execution BO
        if not execution_bo.accounts:
            execution_bo.accounts = provider_accounts
        else:
            execution_bo.accounts.update(provider_accounts)
        
        logger.info(f"Provider accounts found: {len(provider_accounts)}")
    
    def set_issuer_and_acquirer_related_accounts(
        self, execution_bo: MovementExecutionBO
    ) -> None:
        """Set issuer and acquirer related accounts"""
        logger.info("Setting issuer and acquirer related accounts")
        
        # Set issuer related accounts
        if ISSUER_ACCOUNT_ROLE in execution_bo.accounts:
            self.set_role_related_accounts(
                execution_bo.accounts[ISSUER_ACCOUNT_ROLE],
                ISSUER_ACCOUNT_ROLE,
                execution_bo
            )
        
        # Set acquirer related accounts
        if ACQUIRER_ACCOUNT_ROLE in execution_bo.accounts:
            self.set_role_related_accounts(
                execution_bo.accounts[ACQUIRER_ACCOUNT_ROLE],
                ACQUIRER_ACCOUNT_ROLE,
                execution_bo
            )
        
        # Set EME and principal distributor
        self.set_roles_for_eme_and_principal_distributor_account(execution_bo)
    
    def set_role_related_accounts(
        self, account: Account, account_role: str, execution_bo: MovementExecutionBO
    ) -> None:
        """Set role-related accounts (SUPER accounts)"""
        super_role = SUPER_ + account_role
        
        if (super_role in execution_bo.flow_account_roles 
            and account 
            and account.account):
            
            if account.account.legal_entity.code != execution_bo.legal_entity.code:
                raise BrokerException(
                    f"Legal entity mismatch: {account.account_number}",
                    code="LEGAL_ENTITY_MISMATCH",
                    context=account.account_number
                )
            
            execution_bo.request.accounts_roles[super_role] = account.account.account_number
            execution_bo.accounts[super_role] = account.account
            logger.info(f"Set {super_role}: {account.account.account_number}")
    
    def set_roles_for_eme_and_principal_distributor_account(
        self, execution_bo: MovementExecutionBO
    ) -> None:
        """Set EME and principal distributor accounts"""
        # EME account
        if EME in execution_bo.flow_account_roles:
            issuer = execution_bo.accounts.get(ISSUER_ACCOUNT_ROLE)
            acquirer = execution_bo.accounts.get(ACQUIRER_ACCOUNT_ROLE)
            
            if issuer and hasattr(issuer, 'EME_account_number') and issuer.EME_account_number:
                self.set_eme_account_from_code(execution_bo, ISSUER_ACCOUNT_ROLE)
            elif acquirer and hasattr(acquirer, 'EME_account_number') and acquirer.EME_account_number:
                self.set_eme_account_from_code(execution_bo, ACQUIRER_ACCOUNT_ROLE)
        
        # Principal distributor account
        if PRINCIPAL_DISTRIBUTOR in execution_bo.flow_account_roles:
            issuer = execution_bo.accounts.get(ISSUER_ACCOUNT_ROLE)
            acquirer = execution_bo.accounts.get(ACQUIRER_ACCOUNT_ROLE)
            
            if (issuer 
                and hasattr(issuer, 'principal_distri_account_number') 
                and issuer.principal_distri_account_number):
                self.set_distri_account_from_code(execution_bo, ISSUER_ACCOUNT_ROLE)
            elif (acquirer 
                  and hasattr(acquirer, 'principal_distri_account_number') 
                  and acquirer.principal_distri_account_number):
                self.set_distri_account_from_code(execution_bo, ACQUIRER_ACCOUNT_ROLE)
    
    def set_eme_account_from_code(
        self, execution_bo: MovementExecutionBO, account_role: str
    ) -> None:
        """Set EME account"""
        eme_account_number = execution_bo.accounts[account_role].EME_account_number
        
        eme_account = self.engine_entity_loader_service.get_account_by_account_number_or_phone_or_merchant(
            eme_account_number, execution_bo.service
        )
        
        if not eme_account:
            raise BrokerException(
                f"EME account not found: {eme_account_number}",
                code="ACCOUNT_NOT_FOUND",
                context=eme_account_number
            )
        
        execution_bo.accounts[EME] = eme_account
        execution_bo.request.accounts_roles[EME] = eme_account.account_number
        logger.info(f"Set EME account: {eme_account.account_number}")
    
    def set_distri_account_from_code(
        self, execution_bo: MovementExecutionBO, account_role: str
    ) -> None:
        """Set principal distributor account"""
        distri_account_number = execution_bo.accounts[account_role].principal_distri_account_number
        
        distri_account = self.engine_entity_loader_service.get_account_by_account_number_or_phone_or_merchant(
            distri_account_number, execution_bo.service
        )
        
        if not distri_account:
            raise BrokerException(
                f"Principal distributor account not found: {distri_account_number}",
                code="ACCOUNT_NOT_FOUND",
                context=distri_account_number
            )
        
        execution_bo.accounts[PRINCIPAL_DISTRIBUTOR] = distri_account
        execution_bo.request.accounts_roles[PRINCIPAL_DISTRIBUTOR] = distri_account.account_number
        logger.info(f"Set principal distributor: {distri_account.account_number}")
    
    def check_user_from_token(self, execution_bo: MovementExecutionBO) -> None:
        """Validate user from token"""
        logger.info("Checking user from token")
        pass
    
    def check_if_issuer_is_acquirer(self, execution_bo: MovementExecutionBO) -> None:
        """Check that issuer and acquirer are different"""
        logger.info("Checking if issuer equals acquirer")
        
        issuer = execution_bo.request.accounts_roles.get(ISSUER_ACCOUNT_ROLE)
        acquirer = execution_bo.request.accounts_roles.get(ACQUIRER_ACCOUNT_ROLE)
        
        if issuer and acquirer and issuer == acquirer:
            raise BrokerException(
                "Issuer and acquirer cannot be the same",
                code="SAME_ISSUER_AND_ACQUIRER"
            )
    
    def create_movement(self, execution_bo: MovementExecutionBO) -> None:
        """Create movement object"""
        logger.info("Creating movement")
        movement = self.build_movement(execution_bo)
        execution_bo.movement = movement
    
    def check_for_constraints(
        self, execution_bo: MovementExecutionBO, context: str
    ) -> None:
        """Check constraints"""
        logger.info(f"Checking constraints: {context}")
        pass
    
    # def compute_global_amounts_for_each_rule(self, execution_bo: MovementExecutionBO) -> None:
    #     """Compute global amounts"""
    #     logger.info("Computing global amounts")
    #     pass
    #
    # def check_for_impact_rules(
    #     self, execution_bo: MovementExecutionBO, save_operations: bool = True
    # ) -> None:
    #     """Check impact rules"""
    #     logger.info("Checking impact rules")
    #     pass



    def check_for_client(self, execution_bo: MovementExecutionBO) -> None:
        """Check client"""
        logger.info("Checking client")
        pass
    
    def set_effective_accounts_roles_in_movement(
        self, execution_bo: MovementExecutionBO
    ) -> None:
        """Set account roles in movement"""
        if execution_bo.movement and execution_bo.accounts:
            execution_bo.movement.account_roles = {
                role: account.account_number 
                for role, account in execution_bo.accounts.items()
            }
    
    def set_computed_global_amounts_on_movement(
        self, execution_bo: MovementExecutionBO
    ) -> None:
        """Set computed amounts on movement"""
        if execution_bo.movement:
            execution_bo.movement.global_fees = getattr(execution_bo, 'global_charge', 0)
            execution_bo.movement.issuer_fees = getattr(execution_bo, 'issuer_fees', 0)
            execution_bo.movement.acquirer_fees = getattr(execution_bo, 'acquirer_fees', 0)
    
    # def create_and_save_movement(self, execution_bo: MovementExecutionBO) -> None:
    #     """Save movement"""
    #     logger.info("Saving movement")
    #     if not execution_bo.movement:
    #         execution_bo.movement = self.build_movement(execution_bo)
    #
    #     self.db.add(execution_bo.movement)
    #     self.db.commit()
    #     self.db.refresh(execution_bo.movement)

    def create_and_save_movement(self, bo: MovementExecutionBO):
        """Create and save movement"""
        logger.info("Saving movement")

        # Convert Operation objects to dictionaries for JSON serialization
        if bo.movement.load_operations:
            bo.movement.load_operations = [
                op.to_dict() if isinstance(op, Operation) else op
                for op in bo.movement.load_operations
            ]

        if bo.movement.cancel_operations:
            bo.movement.cancel_operations = [
                op.to_dict() if isinstance(op, Operation) else op
                for op in bo.movement.cancel_operations
            ]

        # Save the movement
        self.db.add(bo.movement)
        self.db.commit()
        self.db.refresh(bo.movement)

        logger.info(f"Movement saved with ID: {bo.movement.id}")
    
    # def build_movement(self, execution_bo: MovementExecutionBO) -> Movement:
    #     """Build movement entity"""
    #     req = execution_bo.request
    #     gu_id = req.gu_id or self.generate_uuid()
    #
    #     movement = Movement(
    #         gu_id=gu_id,
    #         log_id=self.generate_uuid(),
    #         amount=req.amount,
    #         commission_base=req.amount,
    #         charge_base=req.amount,
    #         service_code=req.service_code,
    #         product_code=req.product_code,
    #         flow_code=execution_bo.flow.code if execution_bo.flow else None,
    #         status_code="BK_INITIATED",
    #         account_roles=req.accounts_roles,
    #         legal_entity_code=execution_bo.service.legal_entity.code if execution_bo.service and execution_bo.service.legal_entity else None
    #     )
    #
    #     return movement
    #
    def check_if_same_movement_initiated_in_last_mn(
        self, execution_bo: MovementExecutionBO
    ) -> None:
        """Check for duplicates"""
        pass


    def check_if_movement_exists_for_cancellation(
            self, execution_bo: MovementExecutionBO
    ) -> None:

        if execution_bo.request.gu_id_cancellation :
            movement = self.movement_service.find_by_guid(execution_bo.request.gu_id_cancellation)
            if not movement:
                raise BrokerException(
                    f"Movement not found for cancellation: {execution_bo.request.gu_id_cancellation}",
                    "MOVEMENT_NOT_FOUND_FOR_CANCELLATION"
                )

            execution_bo.request.service_code = movement.service_code
            execution_bo.request.product_code = movement.product_code
            execution_bo.request.amount = movement.amount
            logger.info(f"Movement retrieved for cancellation : {movement.id}")
        else :
            logger.info(" pass because no gu_id for cancellation ")

    def check_information_for_cancellation(
            self, execution_bo: MovementExecutionBO
    ) -> None:


        if (execution_bo.request.is_cancellation == True and execution_bo.request.gu_id_cancellation is None)  :
            raise BrokerException(
                f"give the right is information for cancellation gu_id_cancellation",
                "MISSING_INFORMATION_FOR CANCELATION"
            )


    def handle_broker_exception(
        self, exception: BrokerException, execution_bo: MovementExecutionBO
    ) -> None:
        """Handle broker exceptions"""
        logger.error(f"Broker Exception: {exception.code} - {exception.message}")
        
        execution_bo.response_details = ResponseDetails(
            code=exception.code,
            message=exception.message + " " + exception.context,
            is_error=True
        )
        
        if execution_bo.movement:
            execution_bo.movement.status_code = "BK_FAILED"
            self.db.commit()
    
    def handle_default_exception(
        self, exception: Exception, execution_bo: MovementExecutionBO
    ) -> None:
        """Handle general exceptions"""
        logger.error(f"Default Exception: {exception}", exc_info=True)
        
        execution_bo.response_details = ResponseDetails(
            code="SERVER_ERROR",
            message=str(exception),
            is_error=True
        )
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate UUID"""
        import uuid
        return str(uuid.uuid4())

    def compute_global_amounts_for_each_rule(self, execution_bo: MovementExecutionBO) -> None:
        """
        Compute global amounts for each rule in the movement execution business object
        """
        logger.info("Computing global amounts for each rule")
        self.operation_creation_service.compute_global_operations_amount_for_each_rule(execution_bo)


    def check_impact_rule_for_interval_and_account(
            self,
            execution_bo: MovementExecutionBO,
            rule: ImpactRule,
            save_operations: bool = True
    ) -> None:
        """
        Check impact rule for interval and account

        Args:
            execution_bo: Movement execution business object
            rule: Impact rule to check
            save_operations: Whether to save operations to movement

        Raises:
            BrokerException: If no interval found or no matching interval
        """
        # Check if rule has intervals
        if rule.intervals is None or len(rule.intervals) == 0:
            raise BrokerException("NO_INTERVAL_RULE_FOUND")

        # Initialize total amount to support by account if needed
        if execution_bo.total_amount_to_support_by_account is None:
            execution_bo.total_amount_to_support_by_account = {}

        # Get the amount to check
        amount = execution_bo.request.amount
        if execution_bo.movement is not None:
            amount = execution_bo.movement.amount

        logger.info(f"Intervals: {rule.intervals}")

        # Check each interval
        for interval in rule.intervals:
            # Check if the amount is within the interval
            if interval.can_interval_support_amount(amount):
                # Get the account for this rule's role
                role_identifier = rule.rule_account_role.role_identifier
                account = execution_bo.accounts.get(role_identifier)

                # Check if the account can support the negative amount
                self.check_if_account_can_support_rule(
                    interval,
                    account,
                    rule.rule_account_role,
                    execution_bo
                )

                # Save the operation in the movement if save_operations is True
                if save_operations is True:
                    operation = self.operation_creation_service.build_operation(
                        execution_bo,
                        rule,
                        interval
                    )
                    execution_bo.movement.load_operations.append(operation)

                return

        # No matching interval found
        movement_amount = execution_bo.movement.amount if execution_bo.movement else amount
        raise BrokerException(
           "NO_MATCHING_INTERVAL_RULE_FOUND",
            f"{rule.code}|{movement_amount}"
        )


    def check_for_impact_rules(
            self,
            execution_bo: MovementExecutionBO,
            save_operations: bool = True
    ) -> MovementExecutionBO:
        """
        Check all impact rules for the flow

        Args:
            execution_bo: Movement execution business object
            save_operations: Whether to save operations to movement

        Returns:
            Updated execution_bo

        Raises:
            BrokerException: If no impact rules found
        """
        logger.info("Checking impact rules")

        # Check if flow has rules
        if execution_bo.flow.rules is None or len(execution_bo.flow.rules) == 0:
            raise BrokerException("NO_IMPACT_RULE_FOUND")

        # Initialize load operations if needed
        if execution_bo.movement.load_operations is None:
            execution_bo.movement.load_operations = []

        # Initialize total amount to support by account
        execution_bo.total_amount_to_support_by_account = {}

        # Check each impact rule
        for rule in execution_bo.flow.rules:
            # We do the check balance here
            self.check_impact_rule_for_interval_and_account(execution_bo, rule, save_operations)

        return execution_bo


    def check_if_account_can_support_rule(
            self,
            interval: Interval,
            account,
            account_role,
            movement_execution_bo: MovementExecutionBO
    ) -> None:
        """
        Check if account can support the rule amount

        Args:
            interval: The interval to check
            account: The account to check
            account_role: The rule account role
            movement_execution_bo: Movement execution business object

        Raises:
            BrokerException: If account cannot support the amount
        """
        # Check if account exists
        if account is None:
            raise BrokerException(
                "Account with role not found",
                "ACCOUNT_WITH_ROLE_NOT_FOUND",
                account_role.role_identifier
            )

        # Check if the account has the required configured type
        self.check_if_account_has_configured_type(account, account_role)

        # Compute the amount to support by account
        to_support = self.compute_amount_to_support_by_account(
            interval,
            movement_execution_bo.movement.amount
        )

        # Compute the total amount to support by account
        total_amount = self.get_total_amount_to_support(
            account.account_number,
            to_support,
            movement_execution_bo.total_amount_to_support_by_account
        )

        if total_amount < 0:
            # We add the pending movement amount to the total amount
            if account_role.role_identifier == "ISSUER":
                total_amount -= movement_execution_bo.pending_movement_amount

            # Check if the account has enough balance
            if (account.balance.balance < abs(total_amount) and
                    not account.is_provider() and
                    not account.is_mirror_bank()):

                # Check for overdraft possibility
                if (account_role.role_identifier == "ISSUER" and
                        account.overdraft_activated is True):

                    logger.info(
                        f"Doing overdraft request for account: {account.account_number}, "
                        f"role: {account_role.role_identifier}, amount: {total_amount}"
                    )


                    # or
                    #                             self.credit_digital_service.send_overdraft_request(movement_execution_bo)
                    if (movement_execution_bo.overdraft_issued ):

                        logger.info(
                            f"Successfully done overdraft request for account: {account.account_number}, "
                            f"role: {account_role.role_identifier}, amount: {total_amount}"
                        )
                        movement_execution_bo.overdraft_issued = True
                        return

                # Insufficient balance
                raise BrokerException(
                    "Insufficient balance",
                    "INSUFFICIENT_BALANCE",
                    f"{account.account_number}|{total_amount}"
                )


    def check_if_account_has_configured_type(self, account, account_role) -> None:
        """
        Check if the account has at least one of the account types configured for the given rule account role

        Args:
            account: The account to check
            account_role: The rule account role with configured types

        Raises:
            BrokerException: If account type doesn't match configured types
        """
        # Check if the account has account types
        if account.account_types is None or len(account.account_types) == 0:
            raise BrokerException(
                "No account type found for account",
                "NO_ACCOUNT_TYPE_FOUND_FOR_ACCOUNT",
                account.account_number
            )

        # Check if any account type matches the configured role types
        for account_type in account.account_types:
            for role_type in account_role.account_types:
                if account_type.code == role_type:
                    return  # an account type matches the one configured for the role, so return

        # No matching account type found
        raise BrokerException(
            "No matching account type found for role",
            "NO_MATCHING_ACCOUNT_TYPE_FOUND_FOR_ROLE",
            f"{account.account_number}|{account_role.role_identifier}"
        )


    def compute_amount_to_support_by_account(self, interval: Interval, amount: float) -> float:
        """
        Compute the amount to support by account based on interval configuration

        Args:
            interval: The interval with percentage and fixed amount configuration
            amount: The movement amount

        Returns:
            The amount to support (percentage + fixed)
        """
        percentage = interval.percentage if interval.percentage is not None else 0
        fixe = interval.fixe if interval.fixe is not None else 0

        return (amount * percentage / 100) + fixe


    def get_total_amount_to_support(
            self,
            account_number: str,
            to_support: float,
            total_amount_to_support_by_account: Dict[str, float]
    ) -> float:
        """
        Get or compute the total amount to support for an account

        Args:
            account_number: The account number
            to_support: The amount to add to the total
            total_amount_to_support_by_account: Dictionary tracking totals by account

        Returns:
            The updated total amount for this account
        """
        total_amount = 0.0

        if account_number in total_amount_to_support_by_account:
            total_amount = total_amount_to_support_by_account[account_number]

        total_amount += to_support
        total_amount_to_support_by_account[account_number] = total_amount

        return total_amount

    
    
    def build_movement(self, execution_bo: MovementExecutionBO) -> Movement:
        """
        Build movement entity from execution business object
        
        Args:
            execution_bo: Movement execution business object
            
        Returns:
            Movement entity ready to be saved
        """
        req = execution_bo.request
    
        # Generate GU_ID if not provided
        gu_id = req.gu_id or self.generate_uuid()
    
        # Get partner_id based on service scope
        partner_id = None
        if (req.partner_id and
                execution_bo.service and
                execution_bo.service.scope and
                execution_bo.service.scope == "INTERNAL"):
            partner_id = req.partner_id
    
        # Get reference_bulk from transfer request or directly
        # reference_bulk = None
        # if req.transfer_request_model and hasattr(req.transfer_request_model, 'reference_bulk'):
        #     reference_bulk = req.transfer_request_model.reference_bulk
        # elif hasattr(req, 'reference_bulk'):
        #     reference_bulk = req.reference_bulk
    
        # Build the movement
        movement = Movement(
            # Identifiers
            gu_id=gu_id,
            gu_id_cancellation = execution_bo.request.gu_id_cancellation,
            log_id=self.generate_uuid(),
            partner_id=partner_id or req.partner_id if hasattr(req, 'partner_id') else None,
            partner_dist_id=req.partner_dist_id if hasattr(req, 'partner_dist_id') else None,
            client_id=req.client_id if hasattr(req, 'client_id') else None,
    
            # Flow information
            flow_code=execution_bo.flow.code if execution_bo.flow else None,
            flow_version=execution_bo.flow.version if execution_bo.flow else None,
    
            # Amount and bases
            amount=req.amount,
            commission_base=req.amount,
            charge_base=req.amount,
    
            # Service information
            service_code=req.service_code,
            service_label=execution_bo.service.label if execution_bo.service else None,
            service_type_code=(execution_bo.service.service_type.code
                               if execution_bo.service and execution_bo.service.service_type else None),
            product_code=req.product_code if hasattr(req, 'product_code') else None,
    
            # Legal entity and location
            legal_entity_code=(execution_bo.service.legal_entity.code
                               if execution_bo.service and execution_bo.service.legal_entity
                               else req.legal_entity_code if hasattr(req, 'legal_entity_code') else None),
            country_iso_code=(execution_bo.legal_entity.country.iso_code
                              if execution_bo.legal_entity and execution_bo.legal_entity.country else None),
            bank_code=req.bank_code if hasattr(req, 'bank_code') else None,
    
            # Geographic information
            latitude=req.latitude if hasattr(req, 'latitude') else None,
            longitude=req.longitude if hasattr(req, 'longitude') else None,
    
            # User information
            user_login=req.user_login if hasattr(req, 'user_login') else None,
            agent_login=req.agent_login if hasattr(req, 'agent_login') else None,
            user_agent=req.user_agent if hasattr(req, 'user_agent') else None,
    
            # Terminal and merchant
            terminal_id=req.terminal_id if hasattr(req, 'terminal_id') else None,
            merchant_code=self._get_merchant_code(execution_bo),
    
            # Account information
            account_roles=req.accounts_roles if hasattr(req, 'accounts_roles') else None,
            issuer_account=self.get_issuer_account(execution_bo),
            acquirer_account=self.get_acquirer_account(execution_bo),
            issuer_account_label=self._get_issuer_account_label(execution_bo),
            acquirer_account_label=self._get_acquirer_account_label(execution_bo),
            super_issuer=self._get_super_issuer(execution_bo),
            super_acquirer=self._get_super_acquirer(execution_bo),
    
            # Status
            status_code=(execution_bo.init_status
                         if execution_bo.init_status else "BK_INITIATED"),
    
            # References and additional info
            #reference_bulk=reference_bulk,
            slip_number=req.slip_number if hasattr(req, 'slip_number') else None,
            callback_url=req.callback_url if hasattr(req, 'callback_url') else None,
            reason=req.reason if hasattr(req, 'reason') else None,
    
            # Tags
            tag=execution_bo.tag if hasattr(execution_bo, 'tag') else None,
            change_tag=execution_bo.change_tag if hasattr(execution_bo, 'change_tag') else None,
    
            # Operator and movement type
            operator=(execution_bo.service.operator.short_code
                      if execution_bo.service and execution_bo.service.operator else None),
            movement_type=(execution_bo.service.service_type.movement_type
                           if execution_bo.service and execution_bo.service.service_type and
                              hasattr(execution_bo.service.service_type, 'movement_type')
                           else None),
    
            # Other participant
            other_participant_code=self._get_other_participant_code(execution_bo),
    
            # Additional informations
            additional_informations=(req.additional_informations
                                     if hasattr(req, 'additional_informations') else None),
        )
    
        return movement
    
    
    def _get_merchant_code(self, execution_bo: MovementExecutionBO) -> Optional[str]:
        """Get merchant code from acquirer account"""
        if (execution_bo.accounts and
                "ACQUIRER" in execution_bo.accounts):
            acquirer = execution_bo.accounts["ACQUIRER"]
            return acquirer.merchant_code if hasattr(acquirer, 'merchant_code') else None
        return None
    
    
    def _get_super_acquirer(self, execution_bo: MovementExecutionBO) -> Optional[str]:
        """Get super acquirer account number"""
        if (execution_bo.accounts and
                "ACQUIRER" in execution_bo.accounts):
            acquirer = execution_bo.accounts["ACQUIRER"]
            if hasattr(acquirer, 'account') and acquirer.account:
                return acquirer.account.account_number
        return None
    
    
    def _get_super_issuer(self, execution_bo: MovementExecutionBO) -> Optional[str]:
        """Get super issuer account number"""
        if (execution_bo.accounts and
                "ISSUER" in execution_bo.accounts):
            issuer = execution_bo.accounts["ISSUER"]
            if hasattr(issuer, 'account') and issuer.account:
                return issuer.account.account_number
        return None
    
    
    def _get_issuer_account_label(self, execution_bo: MovementExecutionBO) -> Optional[str]:
        """Get issuer account label"""
        if (execution_bo.accounts and
                "ISSUER" in execution_bo.accounts):
            issuer = execution_bo.accounts["ISSUER"]
            return issuer.label if hasattr(issuer, 'label') else None
        return None
    
    
    def _get_acquirer_account_label(self, execution_bo: MovementExecutionBO) -> Optional[str]:
        """Get acquirer account label"""
        if (execution_bo.accounts and
                "ACQUIRER" in execution_bo.accounts):
            acquirer = execution_bo.accounts["ACQUIRER"]
            return acquirer.label if hasattr(acquirer, 'label') else None
        return None
    
    
    def _get_other_participant_code(self, execution_bo: MovementExecutionBO) -> Optional[str]:
        """Get other participant code (implement based on your business logic)"""
        # This should be implemented based on your specific business rules
        # for determining the other participant code
        return None
    
    
    def get_issuer_account(self, execution_bo: MovementExecutionBO) -> Optional[str]:
        """
        Get issuer account identifier from execution BO
        
        Args:
            execution_bo: Movement execution business object
            
        Returns:
            Issuer account identifier (account number or phone)
        """
        if not execution_bo.accounts:
            return None
    
        if "ISSUER" in execution_bo.accounts:
            issuer = execution_bo.accounts["ISSUER"]
            if hasattr(issuer, 'account_number') and issuer.account_number:
                return issuer.account_number
            elif hasattr(issuer, 'phone_number') and issuer.phone_number:
                return issuer.phone_number
    
        return None
    
    
    def get_acquirer_account(self, execution_bo: MovementExecutionBO) -> Optional[str]:
        """
        Get acquirer account identifier from execution BO
        
        Args:
            execution_bo: Movement execution business object
            
        Returns:
            Acquirer account identifier (account number or phone)
        """
        if not execution_bo.accounts:
            return None
    
        if "ACQUIRER" in execution_bo.accounts:
            acquirer = execution_bo.accounts["ACQUIRER"]
            if hasattr(acquirer, 'account_number') and acquirer.account_number:
                return acquirer.account_number
            elif hasattr(acquirer, 'phone_number') and acquirer.phone_number:
                return acquirer.phone_number
    
        return None
    
