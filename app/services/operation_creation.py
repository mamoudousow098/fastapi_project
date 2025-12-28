"""
Operation Creation Service - Equivalent to OperationCreationServiceBean
"""
import logging
from typing import List, Set
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.operation import Operation, OperationDirection
from app.models.movement import Movement
from app.models.impact_rule import ImpactRule
from app.models.interval import Interval
from app.models.enums import StatusEnum, CommissionBaseEnum
from app.schemas.financial.movement import MovementExecutionBO
from app.services.engine_entity_loader import EngineEntityLoaderService
from app.services.movement import MovementService

logger = logging.getLogger(__name__)

# Constants
PROVIDER = "PROVIDER"
COMMISSION_IMPACT_RULE_TYPE = "COMMISSION"
CHARGE_IMPACT_RULE_TYPE = "CHARGE"
ISSUER_ACCOUNT_ROLE = "ISSUER"
ACQUIRER_ACCOUNT_ROLE = "ACQUIRER"
CUSTOMERAPP = "CUSTOMERAPP"
CHANGE_TAG = "CHANGE"
CHANGE_TAG_WITHDRAWAL = "WITHDRAWAL"
CHANGE_TAG_DEPOSIT = "DEPOSIT"


class OperationCreationException(Exception):
    """Exception for operation creation errors"""
    def __init__(self, message: str, code: str = "OPERATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class OperationCreationService:
    """Service for creating and managing operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.engine_entity_loader = EngineEntityLoaderService(db)
        self.movement_service = MovementService(db)
    
    def create_operations_and_update_movement_status(
        self, execution_bo: MovementExecutionBO
    ) -> MovementExecutionBO:
        """
        Create operations and update movement status
        """
        try:
            logger.info("Creating operations and updating movement status")
            self.create_operation(execution_bo)
            self.update_movement_status(execution_bo)
        except Exception as e:
            logger.error(f"Error creating operations: {e}", exc_info=True)
        
        return execution_bo
    
    def create_operation(self, execution_bo: MovementExecutionBO) -> MovementExecutionBO:
        """
        Create operations for the movement
        """
        logger.info("Creating operations")
        
        # Check if cancellation or load operations
        if (execution_bo.movement.status_code == StatusEnum.CANCELLATION_REQUEST.value 
            and (not execution_bo.movement.cancel_operations or not execution_bo.movement.cancel_operations)):
            raise OperationCreationException("Operations not found", "OPERATIONS_NOT_FOUND")
        elif (not execution_bo.movement.load_operations or not execution_bo.movement.load_operations):
            raise OperationCreationException("Operations not found", "OPERATIONS_NOT_FOUND")
        
        try:
            # Select operations to save
            if execution_bo.movement.status_code == StatusEnum.CANCELLATION_REQUEST.value:
                operations = execution_bo.movement.cancel_operations
            else:
                operations = execution_bo.movement.load_operations
            
            # Bulk save operations
            self.bulk_save(operations)
            logger.info(f"Successfully created {len(operations)} operations")
            
        except Exception as e:
            logger.error(f"Error creating operations: {e}", exc_info=True)
            if "ConstraintViolationException" in str(e) or "duplicate" in str(e).lower():
                raise OperationCreationException("Duplicated impact", "DUPLICATED_IMPACT")
            raise
        
        return execution_bo
    
    def build_operation(
        self,
        execution_bo: MovementExecutionBO,
        rule: ImpactRule,
        interval: Interval
    ) -> Operation:
        """
        Build an operation from rule and interval
        """
        logger.info(f"Building operation for rule: {rule.code}")
        
        # Compute amount
        compute_base = self.get_compute_base(rule, execution_bo.movement)
        amount = self.compute_amount_to_support_by_account(interval, compute_base)
        
        # Get account
        account = execution_bo.accounts.get(rule.rule_account_role.role_identifier)
        
        # Handle CUSTOMERAPP special cases
        if (execution_bo.movement.product_code == CUSTOMERAPP 
            and rule.impact_rule_type 
            and rule.impact_rule_type.code == CHARGE_IMPACT_RULE_TYPE
            and (rule.rule_account_role.role_identifier == ISSUER_ACCOUNT_ROLE 
                 or rule.rule_account_role.role_identifier == ACQUIRER_ACCOUNT_ROLE)):
            logger.info(f"Charge amount (no rounded): {amount}")
            amount = self.set_comm_and_fees(execution_bo, amount)
            amount = amount if amount < 0 else -amount
            logger.info(f"Charge amount (rounded): {amount}")
        
        if (execution_bo.movement.product_code == CUSTOMERAPP 
            and rule.impact_rule_type 
            and rule.impact_rule_type.code == COMMISSION_IMPACT_RULE_TYPE):
            logger.info(f"Commission amount: {amount}")
            amount = self.set_comm_and_fees(execution_bo, amount)
            logger.info(f"Commission amount (rounded): {amount}")
        
        # Build operation
        operation = Operation(
            user_login=execution_bo.movement.user_login,
            amount=amount,
            account_number=account.account_number,
            super_account_number=account.account.account_number if account.account else None,
            account_role=rule.rule_account_role.role_identifier,
            gu_id=execution_bo.movement.gu_id,
            operation_direction=OperationDirection.CREDIT if amount > 0 else OperationDirection.DEBIT,
            legal_entity_code=execution_bo.movement.legal_entity_code,
            product_code=execution_bo.movement.product_code,
            impact_rule_code=rule.impact_rule_type.code,
            op_date=datetime.now(),
            balance_id=account.balance.id if account.balance else None,
            global_fees=execution_bo.global_charge if hasattr(execution_bo, 'global_charge') else 0,
            issuer_fees=execution_bo.issuer_fees if hasattr(execution_bo, 'issuer_fees') else 0,
            acquirer_fees=execution_bo.acquirer_fees if hasattr(execution_bo, 'acquirer_fees') else 0,
            global_commission=execution_bo.global_commission if hasattr(execution_bo, 'global_commission') else 0,
            issuer_commissions=execution_bo.issuer_commission if hasattr(execution_bo, 'issuer_commission') else 0,
            acquirer_commissions=execution_bo.acquirer_commission if hasattr(execution_bo, 'acquirer_commission') else 0,
            partner_dist_id=execution_bo.movement.partner_dist_id,
            partner_id=execution_bo.movement.partner_id
        )
        
        return operation
    
    def set_comm_and_fees(self, execution_bo: MovementExecutionBO, amount: float) -> float:
        """Round commission and fees"""
        if (execution_bo.movement 
            and hasattr(execution_bo.movement, 'tag')
            and execution_bo.movement.tag == CHANGE_TAG):
            amount = self.set_change_fees(amount, execution_bo)
        else:
            # Use RoundAmountUtil equivalent
            amount = self.round_fees(amount, False)
        
        return amount
    
    def set_change_fees(self, amount: float, execution_bo: MovementExecutionBO) -> float:
        """Set change fees"""
        if not amount or amount == 0:
            return 0.0
        
        if hasattr(execution_bo, 'change_tag'):
            if execution_bo.change_tag == CHANGE_TAG_WITHDRAWAL:
                amount = execution_bo.change.withdrawal_fees if execution_bo.change else amount
            elif execution_bo.change_tag == CHANGE_TAG_DEPOSIT:
                amount = execution_bo.change.deposit_fees if execution_bo.change else amount
        
        return amount
    
    def round_fees(self, amount: float, round_up: bool = False) -> float:
        """Round fees to nearest multiple of 5"""
        if round_up:
            return round(amount / 5) * 5
        else:
            import math
            return math.floor(amount / 5) * 5
    
    def get_inverse_operations(self, execution_bo: MovementExecutionBO) -> List[Operation]:
        """
        Get inverse operations for cancellation
        """
        logger.info("Getting inverse operations for cancellation")
        
        if not execution_bo.movement.load_operations:
            raise OperationCreationException("Operations not found", "OPERATIONS_NOT_FOUND")
        
        canceled_operations = []
        
        for operation in execution_bo.movement.load_operations:
            canceled_op = Operation(
                user_login=execution_bo.movement.user_login,
                amount=-operation.amount,
                global_fees=operation.global_fees,
                issuer_fees=operation.issuer_fees,
                acquirer_fees=operation.acquirer_fees,
                global_commission=operation.global_commission,
                issuer_commissions=operation.issuer_commissions,
                acquirer_commissions=operation.acquirer_commissions,
                account_number=operation.account_number,
                super_account_number=operation.super_account_number,
                account_role=operation.account_role,
                gu_id=execution_bo.movement.gu_id,
                operation_direction=(
                    OperationDirection.CREDIT 
                    if operation.operation_direction == OperationDirection.DEBIT 
                    else OperationDirection.DEBIT
                ),
                legal_entity_code=operation.legal_entity_code,
                product_code=operation.product_code,
                impact_rule_code=f"CANCELLATION_{operation.impact_rule_code}",
                op_date=datetime.now(),
                balance_id=operation.balance_id
            )
            canceled_operations.append(canceled_op)
        
        logger.info(f"Created {len(canceled_operations)} cancellation operations")
        return canceled_operations
    
    def compute_global_operations_amount_for_each_rule(
        self, execution_bo: MovementExecutionBO
    ) -> MovementExecutionBO:
        """
        Compute global amounts for each impact rule
        """
        logger.info("Computing global operations amount for each rule")
        
        charge_exists = False
        global_commission = 0.0
        global_charge = 0.0
        issuer_commissions = 0.0
        acquirer_commissions = 0.0
        issuer_charge = 0.0
        acquirer_charge = 0.0
        issuer_impact = 0.0
        acquirer_impact = 0.0
        
        indexes_of_commissions_to_recompute: Set[int] = set()
        
        index = -1
        for rule in execution_bo.flow.rules:
            index += 1
            
            # Skip provider rules
            if PROVIDER in rule.rule_account_role.role_identifier:
                continue
            
            # Compute amount
            amount = self.find_interval_and_compute_impact_amount(
                execution_bo.movement.amount,
                self.get_compute_base(rule, execution_bo.movement),
                rule
            )
            
            rule_code = rule.impact_rule_type.code
            role_identifier = rule.rule_account_role.role_identifier
            
            # Handle commission base on fees
            if (COMMISSION_IMPACT_RULE_TYPE in rule_code
                and execution_bo.flow.commission_base == CommissionBaseEnum.FEES_AMOUNT):
                indexes_of_commissions_to_recompute.add(index)
                continue
            
            # Compute impacts
            if role_identifier == ACQUIRER_ACCOUNT_ROLE:
                acquirer_impact += amount
            elif role_identifier == ISSUER_ACCOUNT_ROLE:
                issuer_impact += amount
            
            # Handle charges
            if CHARGE_IMPACT_RULE_TYPE in rule_code:
                charge_exists = True
                fees_amount = amount
                logger.info(f"{CHARGE_IMPACT_RULE_TYPE}: {fees_amount}")
                
                if (execution_bo.movement 
                    and execution_bo.movement.product_code == CUSTOMERAPP):
                    fees_amount = self.set_comm_and_fees(execution_bo, fees_amount)
                    fees_amount = fees_amount if fees_amount < 0 else -fees_amount
                    logger.info(f"{CHARGE_IMPACT_RULE_TYPE} (rounded): {fees_amount}")
                
                if role_identifier == ISSUER_ACCOUNT_ROLE:
                    issuer_charge += fees_amount
                    logger.info(f"{CHARGE_IMPACT_RULE_TYPE} {ISSUER_ACCOUNT_ROLE}: {issuer_charge}")
                elif role_identifier == ACQUIRER_ACCOUNT_ROLE:
                    acquirer_charge += fees_amount
                    logger.info(f"{CHARGE_IMPACT_RULE_TYPE} {ACQUIRER_ACCOUNT_ROLE}: {acquirer_charge}")
                
                global_charge += fees_amount
                logger.info(f"Global charge {CHARGE_IMPACT_RULE_TYPE}: {global_charge}")
            
            # Handle commissions
            elif COMMISSION_IMPACT_RULE_TYPE in rule_code:
                comm_amount = amount
                logger.info(f"{COMMISSION_IMPACT_RULE_TYPE}: {comm_amount}")
                
                if (charge_exists 
                    and execution_bo.movement 
                    and execution_bo.movement.product_code == CUSTOMERAPP):
                    logger.info(f"{COMMISSION_IMPACT_RULE_TYPE} (before rounding): {comm_amount}")
                    comm_amount = self.set_comm_and_fees(execution_bo, comm_amount)
                
                if role_identifier == ISSUER_ACCOUNT_ROLE:
                    issuer_commissions += comm_amount
                elif role_identifier == ACQUIRER_ACCOUNT_ROLE:
                    acquirer_commissions += comm_amount
                
                global_commission += comm_amount
            
            logger.info(f"Global charge: {global_charge}, Global commission: {global_commission}")
        
        # Recompute commissions based on fees if needed
        if indexes_of_commissions_to_recompute:
            for index_of_commission in indexes_of_commissions_to_recompute:
                rule = execution_bo.flow.rules[index_of_commission]
                amount = self.find_interval_and_compute_impact_amount(
                    execution_bo.movement.amount,
                    -global_charge,
                    rule
                )
                
                if rule.rule_account_role.role_identifier == ISSUER_ACCOUNT_ROLE:
                    issuer_commissions += amount
                    issuer_impact += amount
                elif rule.rule_account_role.role_identifier == ACQUIRER_ACCOUNT_ROLE:
                    acquirer_commissions += amount
                    acquirer_impact += amount
                
                global_commission += amount
            
            execution_bo.movement.commission_base = -global_charge
        
        # Set computed values on execution BO
        execution_bo.issuer_total_impact = issuer_impact
        execution_bo.acquirer_total_impact = acquirer_impact
        execution_bo.global_commission = global_commission
        execution_bo.global_charge = global_charge
        execution_bo.issuer_commission = issuer_commissions
        execution_bo.acquirer_commission = acquirer_commissions
        execution_bo.issuer_fees = issuer_charge
        execution_bo.acquirer_fees = acquirer_charge
        
        logger.info(f"Computed amounts - Issuer impact: {issuer_impact}, Acquirer impact: {acquirer_impact}")
        
        return execution_bo
    
    def get_compute_base(self, rule: ImpactRule, movement: Movement) -> float:
        """Get the compute base for the rule"""
        if rule.impact_rule_type.code == COMMISSION_IMPACT_RULE_TYPE:
            return movement.commission_base
        elif rule.impact_rule_type.code == CHARGE_IMPACT_RULE_TYPE:
            return movement.charge_base
        else:
            return movement.amount
    
    def find_interval_and_compute_impact_amount(
        self, movement_amount: float, amount: float, rule: ImpactRule
    ) -> float:
        """Find the right interval and compute impact amount"""
        for interval in rule.intervals:
            if interval.can_interval_support_amount(movement_amount):
                return self.compute_amount_to_support_by_account(interval, amount)
        return 0.0
    
    def compute_amount_to_support_by_account(self, interval: Interval, base_amount: float) -> float:
        """Compute the amount based on interval percentage and fixed"""
        return (interval.percentage / 100) * base_amount + interval.fixe
    
    def update_movement_status(self, execution_bo: MovementExecutionBO) -> MovementExecutionBO:
        """Update movement status after operations creation"""
        logger.info("Updating movement status")
        
        if execution_bo.movement.status_code == StatusEnum.CANCELLATION_REQUEST.value:
            status_enum = StatusEnum.CANCELLED
        else:
            status_enum = StatusEnum.SUCCESSFUL
            execution_bo.movement.impact_date = datetime.now()
        
        # Get status from engine entity loader
        status = self.engine_entity_loader.get_status_by_code(status_enum.value)
        
        # Update status
        self.movement_service.update_status(
            execution_bo.movement,
            status,
            execution_bo.movement.user_login,
            "Operations created"
        )
        
        logger.info(f"Movement status updated to: {status_enum.value}")
        return execution_bo
    
    def bulk_save(self, operations: List[Operation]) -> None:
        """Bulk save operations using raw SQL"""
        try:
            logger.info(f"Bulk saving {len(operations)} operations")
            
            sql = """
            INSERT INTO operation (
                amount, balance_before, balance_after, account_number,
                account_role, gu_id, sens_operation, legal_entity_code, product_code,
                global_comission, global_fees, impact_rule_code, op_date, id_balance,
                user_login, issuer_commissions, acquirer_commissions, issuer_charges, 
                acquirer_charges, super_account_number
            ) VALUES 
            """
            
            # Build values placeholders
            placeholders = []
            params = []
            
            for operation in operations:
                placeholders.append("(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
                params.extend([
                    operation.amount,
                    operation.balance_before,
                    operation.balance_after,
                    operation.account_number,
                    operation.account_role,
                    operation.gu_id,
                    operation.operation_direction.value if operation.operation_direction else None,
                    operation.legal_entity_code,
                    operation.product_code,
                    operation.global_commission,
                    operation.global_fees,
                    operation.impact_rule_code,
                    operation.op_date,
                    operation.balance_id,
                    operation.user_login,
                    operation.issuer_commissions,
                    operation.acquirer_commissions,
                    operation.issuer_fees,
                    operation.acquirer_fees,
                    operation.super_account_number
                ])
            
            sql += ", ".join(placeholders)
            
            # Execute bulk insert
            result = self.db.execute(text(sql), params)
            self.db.commit()
            
            logger.info(f"Bulk save completed: {result.rowcount} rows inserted")
            
        except Exception as e:
            logger.error(f"Error during bulk save: {e}", exc_info=True)
            self.db.rollback()
            raise