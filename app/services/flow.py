"""
Flow service layer - Business logic with cancellation support
"""
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.provider import Provider

logger = logging.getLogger(__name__)

from app.models.flow import Flow
from app.models.impact_rule import ImpactRule
from app.models.constraint import Constraint
from app.models.interval import Interval
from app.models.service import Service
from app.models.product import Product
from app.models.account import Account
from app.models.service_provider import ServiceProvider
from app.models.account_dependency import AccountType
from app.models.account_role import AccountRole
from app.models.impact_rule_type import ImpactRuleType
from app.models.enums import EntityState
from app.schemas.flow import FlowCreate
from app.repositories.flow import FlowRepository
from app.models.rule_account_role import RuleAccountRole


class FlowService:
    """Service for flow business logic"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = FlowRepository(db)

    def get_all_flows(
            self,
            legal_entity: Optional[str] = None,
            code: Optional[str] = None,
            service_code: Optional[str] = None,
            status: Optional[str] = None,
            is_cancellation: Optional[bool] = None,
            page: int = 0,
            size: int = 100
    ) -> List[Flow]:
        """Get all flows with filters"""
        # Convert status string to EntityState if provided
        status_enum = None
        if status:
            try:
                status_enum = EntityState(status)
            except ValueError:
                pass

        return self.repository.get_all(
            legal_entity=legal_entity,
            code=code,
            service_code=service_code,
            status=status_enum,
           # is_cancellation=is_cancellation,
            skip=page * size,
            limit=size
        )

    def get_flow_by_code(self, code: str) -> Optional[Flow]:
        """Get flow by code"""
        return self.repository.get_by_code(code)

    def create_flow(self, flow_data: FlowCreate) -> Flow:
        """Create a new flow with validation"""
        logger.info("=" * 80)
        logger.info("Starting flow creation process")
        logger.info(f"Flow code: {flow_data.code}")
        logger.info(f"Service code: {flow_data.service_code}")
        logger.info(f"Number of rules: {len(flow_data.rules)}")
        logger.info(f"Create cancellation: {flow_data.create_cancellation}")
        logger.info("=" * 80)

        try:
            # Validate service exists
            logger.info(f"Validating service: {flow_data.service_code}")
            service = self.db.query(Service).filter(
                Service.code == flow_data.service_code
            ).first()
            if not service:
                logger.error(f"Service not found: {flow_data.service_code}")
                raise ValueError(f"Service with code '{flow_data.service_code}' not found")
            logger.info(f"Service found: {service.code}")

            # Validate account roles (ACQUIRER or ISSUER required)
            logger.info("Validating account roles...")
            self._check_account_roles(flow_data.rules)
            logger.info("Account roles validated successfully")

            # Validate intervals and rules
            logger.info("Validating impact rules and intervals...")
            self._validate_impact_rules(flow_data.rules, service)
            logger.info("Impact rules validated successfully")

            # Handle products
            logger.info("Processing products...")
            products = self._get_products(flow_data)
            logger.info(f"Products found: {[p.code for p in products] if products else 'None'}")

            # Handle account
            account = None
            if flow_data.account_number:
                logger.info(f"Validating account: {flow_data.account_number}")
                account = self.db.query(Account).filter(
                    Account.account_number == flow_data.account_number
                ).first()
                if not account:
                    logger.error(f"Account not found: {flow_data.account_number}")
                    raise ValueError(f"Account '{flow_data.account_number}' not found")
                logger.info(f"Account found: {account.account_number}")

            # Validate client category if provided
            if flow_data.client_category:
                logger.info(f"Client category: {flow_data.client_category}")

            # Validate exclusive constraints
            logger.info("Validating exclusive constraints...")
            self._validate_exclusive_constraints(products, flow_data)
            logger.info("Exclusive constraints validated")

            # Create flows (one per product if multiple products)
            logger.info("Creating flow instances...")
            flows = []
            if products and len(products) > 1:
                logger.info(f"Creating multiple flows for {len(products)} products")
                # Check if flows already exist for multiple products
                for product in products:
                    test_code = f"{flow_data.code}_{product.code}"
                    if self.repository.exists_by_code(test_code):
                        logger.error(f"Flow already exists: {test_code}")
                        raise ValueError(f"Flow with code '{test_code}' already exists")

                for product in products:
                    logger.info(f"Creating flow for product: {product.code}")
                    flow = self._create_single_flow(
                        flow_data, service, product, account, is_cancellation=False
                    )
                    flows.append(flow)
            else:
                product = products[0] if products else None
                logger.info(f"Creating single flow with product: {product.code if product else 'None'}")
                flow = self._create_single_flow(
                    flow_data, service, product, account, is_cancellation=False
                )
                flows.append(flow)

            # Create cancellation flows if requested
            if flow_data.create_cancellation:
                logger.info("Creating cancellation flows...")
                cancellation_flows = self._create_cancellation_flows(
                    flow_data, service, products, account
                )
                flows.extend(cancellation_flows)
                logger.info(f"Created {len(cancellation_flows)} cancellation flow(s)")

            # Save all flows
            logger.info(f"Saving {len(flows)} flow(s) to database...")
            for flow in flows:
                self.db.add(flow)

            self.db.commit()
            logger.info("Flows committed to database")

            for flow in flows:
                self.db.refresh(flow)

            logger.info("=" * 80)
            logger.info(f"Flow creation completed successfully: {flows[0].code}")
            if flow_data.create_cancellation:
                logger.info(f"Cancellation flow(s) created: {[f.code for f in flows if f.is_cancellation]}")
            logger.info("=" * 80)

            return flows[0]

        except Exception as e:
            logger.error(f"Error during flow creation: {str(e)}", exc_info=True)
            self.db.rollback()
            raise

    def _create_cancellation_flows(
            self,
            flow_data: FlowCreate,
            service: Service,
            products: List[Product],
            account: Optional[Account]
    ) -> List[Flow]:
        """Create cancellation flows with inverted impact rules"""
        logger.info("Creating cancellation flows with inverted rules...")

        # Create inverted flow data for cancellation
        inverted_flow_data = self._invert_flow_data(flow_data)

        cancellation_flows = []

        if products and len(products) > 1:
            for product in products:
                flow = self._create_single_flow(
                    inverted_flow_data, service, product, account, is_cancellation=True
                )
                cancellation_flows.append(flow)
        else:
            product = products[0] if products else None
            flow = self._create_single_flow(
                inverted_flow_data, service, product, account, is_cancellation=True
            )
            cancellation_flows.append(flow)

        return cancellation_flows

    def _invert_flow_data(self, flow_data: FlowCreate) -> FlowCreate:
        """Create a copy of flow_data with inverted impact rule values"""
        from copy import deepcopy
        from app.schemas.flow import ImpactRuleSchema, IntervalSchema

        logger.info("Inverting flow data for cancellation...")

        # Create inverted rules
        inverted_rules = []
        for rule_data in flow_data.rules:
            # Create inverted intervals
            inverted_intervals = []
            for interval in rule_data.intervals:
                inverted_interval = IntervalSchema(
                    minimum_amount=interval.minimum_amount,
                    maximum_amount=interval.maximum_amount,
                    percentage=-interval.percentage,  # Invert percentage
                    fixe=-interval.fixe  # Invert fixe
                )
                inverted_intervals.append(inverted_interval)
                logger.info(
                    f"Inverted interval: percentage {interval.percentage} -> {inverted_interval.percentage}, "
                    f"fixe {interval.fixe} -> {inverted_interval.fixe}"
                )

            # Create inverted rule
            inverted_rule = ImpactRuleSchema(
                code=rule_data.code,
                label=rule_data.label,
                account_role_code=rule_data.account_role_code,
                impact_rule_type_code=rule_data.impact_rule_type_code,
                account_types=rule_data.account_types,
                intervals=inverted_intervals
            )
            inverted_rules.append(inverted_rule)

        # Create new FlowCreate with inverted rules
        inverted_flow_data = FlowCreate(
            code=flow_data.code+"_CANCELLATION",
            label=flow_data.label,
            service_code=flow_data.service_code,
            application_date=flow_data.application_date,
            date_format_application_date=flow_data.date_format_application_date,
            rules=inverted_rules,
            constraints=flow_data.constraints,
            product_code=flow_data.product_code,
            product_codes=flow_data.product_codes,
            account_number=flow_data.account_number,
            client_category=flow_data.client_category,
            commission_base=flow_data.commission_base,
            provider=flow_data.provider,
            create_cancellation=False  # Don't create nested cancellations
        )

        logger.info("Flow data inverted successfully")
        return inverted_flow_data

    def _check_account_roles(self, rules):
        """Check that at least ACQUIRER or ISSUER role is present"""
        ACQUIRER = "ACQUIRER"
        ISSUER = "ISSUER"

        found_acquirer = False
        found_issuer = False

        for rule in rules:
            if rule.account_role_code == ACQUIRER:
                found_acquirer = True
            elif rule.account_role_code == ISSUER:
                found_issuer = True

        if not found_acquirer and not found_issuer:
            raise ValueError("At least one rule must have ACQUIRER or ISSUER role")

    def _validate_impact_rules(self, rules, service):
        """Validate impact rules intervals and sum"""
        if not rules:
            raise ValueError("At least one impact rule is required")

        interval_count = len(rules[0].intervals)

        # Validate each interval across all rules
        for i in range(interval_count):
            total_sum = 0.0
            first_min = rules[0].intervals[i].minimum_amount
            first_max = rules[0].intervals[i].maximum_amount

            for rule in rules:
                if len(rule.intervals) != interval_count:
                    raise ValueError("All rules must have the same number of intervals")

                interval = rule.intervals[i]

                # Check min < max
                if interval.minimum_amount >= interval.maximum_amount:
                    raise ValueError("Maximum amount must be greater than minimum amount")

                # Check all intervals have same min/max
                if interval.minimum_amount != first_min or interval.maximum_amount != first_max:
                    raise ValueError("All intervals at the same position must have the same min and max amounts")

                # Calculate sum (skip for special cases)
                if not self._should_skip_sum_validation(rule, service):
                    total_sum += self._compute_sum(rule, i)

            # Validate sum is zero (with tolerance for floating point)
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"La Somme est : {total_sum}")

            if abs(total_sum) > 0.01:
                raise ValueError(f"The sum of impacts must be zero for each interval. Got {total_sum}")

    def _compute_sum(self, rule, interval_index) -> float:
        """Compute the sum for validation"""
        interval = rule.intervals[interval_index]
        percent = interval.percentage
        minimum_amount = interval.minimum_amount
        maximum_amount = interval.maximum_amount
        fixe = interval.fixe

        value = percent * (minimum_amount + maximum_amount) / 2 + fixe

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"La valeur est : {value}")

        return value

    def _should_skip_sum_validation(self, rule, service) -> bool:
        """Check if sum validation should be skipped for this rule"""
        # Constants from Java code
        MONEY_DESTRUCTION = "MONEY_DESTRUCTION"
        MONEY_CREATION = "MONEY_CREATION"
        BALANCE_MIGRATION = "BALANCE_MIGRATION"
        BANK_SUPPLY = "BANK_SUPPLY"
        EME = "EME"
        PROVIDER = "PROVIDER"
        BANK = "BANK"
        COM_EME = "COM_EME"

        service_type_code = service.service_type.code if service.service_type else None

        # Skip for specific service types and account roles
        if service_type_code in [MONEY_DESTRUCTION, MONEY_CREATION]:
            if rule.account_role_code == EME:
                return True

        if rule.account_role_code == PROVIDER:
            return True

        if service_type_code == BALANCE_MIGRATION:
            if COM_EME in rule.account_types:
                return True

        if service_type_code == BANK_SUPPLY:
            return True

        if rule.account_role_code == BANK:
            return True

        return False

    def _get_products(self, flow_data: FlowCreate) -> List[Product]:
        """Get products from flow data"""
        products = []

        # Handle product_codes set
        product_codes = flow_data.product_codes or set()

        # Add product_code to the set if provided
        if flow_data.product_code:
            product_codes.add(flow_data.product_code)

        # Fetch products
        for code in product_codes:
            product = self.db.query(Product).filter(Product.code == code).first()
            if not product:
                raise ValueError(f"Product with code '{code}' not found")
            products.append(product)

        return products

    def _validate_exclusive_constraints(self, products, flow_data):
        """Validate that only one of products, account, or client_category is set"""
        constraints_set = sum([
            len(products) > 0,
            bool(flow_data.account_number),
            bool(flow_data.client_category)
        ])

        if constraints_set >= 2:
            raise ValueError("Only one of products, account_number, or client_category can be specified")

    def _create_single_flow(
            self,
            flow_data: FlowCreate,
            service: Service,
            product: Optional[Product],
            account: Optional[Account],
            is_cancellation: bool = False
    ) -> Flow:
        """Create a single flow instance"""
        logger.info(f"Creating single flow instance (cancellation={is_cancellation})...")

        # Generate code based on service, product, account, and client category
        product_code = product.code if product else "ALL"
        account_number = account.account_number if account else "ALL"
        client_category = flow_data.client_category if flow_data.client_category else "ALL"

        # Add suffix for cancellation flows
        suffix = "_CANCEL" if is_cancellation else ""
        flow_code = f"{service.code}#{product_code}#{account_number}#{client_category}{suffix}"
        logger.info(f"Generated flow code: {flow_code}")

        # Check if flow already exists
        existing = self.repository.get_by_code(flow_code)
        if existing:
            logger.error(f"Flow already exists: {flow_code}")
            raise ValueError(f"Flow with code '{flow_code}' already exists")

        # Handle application date
        if flow_data.date_format_application_date:
            app_date = flow_data.date_format_application_date
            logger.info(f"Using date_format_application_date: {app_date}")
        elif flow_data.application_date:
            app_date = datetime.fromtimestamp(flow_data.application_date / 1000)
            logger.info(f"Using application_date timestamp: {flow_data.application_date} -> {app_date}")
        else:
            logger.error("No application date provided")
            raise ValueError("Application date is required")

        # Create flow
        logger.info("Creating Flow object...")
        label_suffix = " (Cancellation)" if is_cancellation else ""
        flow = Flow(
            code=flow_code,
            label=f"{flow_data.label}{label_suffix}",
            application_date=app_date,
            service_code=service.code,
            product_code=product.code if product else None,
            account_number=account.account_number if account else None,
            client_category=flow_data.client_category,
            commission_base=flow_data.commission_base,
            status=EntityState.ACTIVE,
            is_cancellation=is_cancellation
        )
        logger.info(f"Flow object created with code: {flow.code}")

        # Create impact rules (inverted for cancellation)
        logger.info(f"Creating {len(flow_data.rules)} impact rules...")
        for idx, rule_data in enumerate(flow_data.rules):
            logger.info(f"Processing rule {idx + 1}: {rule_data.code}")

            # Validate account role exists
            logger.info(f"Validating account role: {rule_data.account_role_code}")
            account_role = self.db.query(AccountRole).filter(
                AccountRole.identifier == rule_data.account_role_code
            ).first()
            if not account_role:
                logger.error(f"Account role not found: {rule_data.account_role_code}")
                raise ValueError(f"Account role not found for code: {rule_data.account_role_code}")

            # Validate impact rule type exists
            logger.info(f"Validating impact rule type: {rule_data.impact_rule_type_code}")
            impact_rule_type = self.db.query(ImpactRuleType).filter(
                ImpactRuleType.code == rule_data.impact_rule_type_code
            ).first()
            if not impact_rule_type:
                logger.error(f"Impact rule type not found: {rule_data.impact_rule_type_code}")
                raise ValueError(f"Impact rule type not found for code: {rule_data.impact_rule_type_code}")

            # Validate account types
            logger.info(f"Validating {len(rule_data.account_types)} account types...")
            for account_type_code in rule_data.account_types:
                account_type = self.db.query(AccountType).filter(
                    AccountType.code == account_type_code
                ).first()
                if not account_type:
                    logger.error(f"Account type not found: {account_type_code}")
                    raise ValueError(f"Account type not found for code: {account_type_code}")

            # Create rule account role
            rule_account_role = RuleAccountRole(
                role_identifier=rule_data.account_role_code,
                account_types=rule_data.account_types
            )

            rule = ImpactRule(
                code=rule_data.code,
                label=rule_data.label,
                rule_account_role=rule_account_role,
                impact_rule_type_id=impact_rule_type.id
            )

            # Create intervals
            logger.info(f"Creating {len(rule_data.intervals)} intervals for rule {rule_data.code}...")
            for interval_data in rule_data.intervals:
                interval = Interval(
                    minimum_amount=interval_data.minimum_amount,
                    maximum_amount=interval_data.maximum_amount,
                    percentage=interval_data.percentage,
                    fixe=interval_data.fixe
                )
                rule.intervals.append(interval)

                if is_cancellation:
                    logger.info(f"Cancellation interval: percentage={interval_data.percentage}, fixe={interval_data.fixe}")

            flow.rules.append(rule)
            logger.info(f"Rule {rule_data.code} added to flow")

        # Create constraints
        if flow_data.constraints:
            logger.info(f"Creating {len(flow_data.constraints)} constraints...")
            for constraint_data in flow_data.constraints:
                constraint = Constraint(
                    code=constraint_data.code,
                    value=constraint_data.value,
                    context=constraint_data.movement_context if hasattr(constraint_data, 'movement_context') else None
                )
                flow.constraints.append(constraint)

        # Create service provider
        if flow_data.provider:
            logger.info(f"Creating service provider: {flow_data.provider.provider}")
            # Validate provider exists

            provider = self.db.query(Provider).filter(
                Provider.code == flow_data.provider.provider
            ).first()
            if not provider:
                logger.error(f"Provider not found: {flow_data.provider.provider}")
                raise ValueError(f"Provider not found for code: {flow_data.provider.provider}")

            service_provider = ServiceProvider(
                provider_id=provider.id,
                url=flow_data.provider.url,
                ranking=flow_data.provider.ranking,
                gateway=flow_data.provider.gateway
            )
            flow.provider = service_provider

        logger.info(f"Single flow instance created successfully: {flow.code}")
        return flow

    def update_flow_status(self, code: str, new_status: EntityState) -> Flow:
        """Update flow status"""
        flow = self.repository.get_by_code(code)
        if not flow:
            raise ValueError(f"Flow with code '{code}' not found")

        flow.status = new_status
        self.db.commit()
        self.db.refresh(flow)

        return flow

    def delete_flow(self, code: str) -> None:
        """Soft delete a flow by setting deleted=True"""
        flow = self.repository.get_by_code(code)
        if not flow:
            raise ValueError(f"Flow with code '{code}' not found")

        flow.deleted = True
        self.db.commit()