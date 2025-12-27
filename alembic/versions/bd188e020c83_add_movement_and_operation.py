"""add movement and operation

Revision ID: bd188e020c83
Revises: b156c8d2b712
Create Date: 2025-12-27 10:27:07.337285

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'bd188e020c83'
down_revision = 'b156c8d2b712'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Créer les nouveaux types ENUM avec checkfirst=True
    from sqlalchemy.dialects.postgresql import ENUM
    
    # Créer movement_type_enum
    movement_type_enum = ENUM(
         'OPERATION', 'TRANSACTION',
        name='movement_type_enum',
        create_type=False
    )
    movement_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Créer operation_direction_enum
    operation_direction_enum = ENUM(
        'CREDIT', 'DEBIT',
        name='operation_direction_enum',
        create_type=False
    )
    operation_direction_enum.create(op.get_bind(), checkfirst=True)
    
    # Créer la table movement
    op.create_table('movement',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('flow_code', sa.String(), nullable=True),
        sa.Column('flow_version', sa.String(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('impact_date', sa.DateTime(), nullable=True),
        sa.Column('sent_date', sa.DateTime(), nullable=True),
        sa.Column('cancellation_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('global_commission', sa.Float(), nullable=True),
        sa.Column('global_fees', sa.Float(), nullable=True),
        sa.Column('issuer_commissions', sa.Float(), nullable=True),
        sa.Column('acquirer_commissions', sa.Float(), nullable=True),
        sa.Column('issuer_charges', sa.Float(), nullable=True),
        sa.Column('acquirer_charges', sa.Float(), nullable=True),
        sa.Column('issuer_impact', sa.Float(), nullable=True),
        sa.Column('acquirer_impact', sa.Float(), nullable=True),
        sa.Column('commission_base', sa.Float(), nullable=True),
        sa.Column('charge_base', sa.Float(), nullable=True),
        sa.Column('gu_id', sa.String(), nullable=True),
        sa.Column('partner_id', sa.String(), nullable=True),
        sa.Column('partner_dist_id', sa.String(), nullable=True),
        sa.Column('client_id', sa.String(), nullable=True),
        sa.Column('merchant_code', sa.String(), nullable=True),
        sa.Column('legal_entity_code', sa.String(), nullable=True),
        sa.Column('bank_code', sa.String(), nullable=True),
        sa.Column('terminal_id', sa.String(), nullable=True),
        sa.Column('log_id', sa.String(), nullable=True),
        sa.Column('country_iso_code', sa.String(), nullable=True),
        sa.Column('latitude', sa.String(), nullable=True),
        sa.Column('longitude', sa.String(), nullable=True),
        sa.Column('user_login', sa.String(), nullable=True),
        sa.Column('agent_login', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('product_code', sa.String(), nullable=True),
        sa.Column('service_code', sa.String(), nullable=True),
        sa.Column('service_label', sa.String(), nullable=True),
        sa.Column('service_type_code', sa.String(), nullable=True),
        sa.Column('issuer_account', sa.String(), nullable=True),
        sa.Column('acquirer_account', sa.String(), nullable=True),
        sa.Column('issuer_account_label', sa.String(), nullable=True),
        sa.Column('acquirer_account_label', sa.String(), nullable=True),
        sa.Column('super_issuer', sa.String(), nullable=True),
        sa.Column('super_acquirer', sa.String(), nullable=True),
        sa.Column('status_code', sa.String(), nullable=True),
        sa.Column('message', sa.String(), nullable=True),
        sa.Column('reject_reason', sa.String(), nullable=True),
        sa.Column('cancellation_reason', sa.String(), nullable=True),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('reference_bulk', sa.String(), nullable=True),
        sa.Column('slip_number', sa.String(), nullable=True),
        sa.Column('callback_url', sa.String(), nullable=True),
        sa.Column('other_participant_code', sa.String(), nullable=True),
        sa.Column('operator', sa.String(), nullable=True),
        sa.Column('tag', sa.String(), nullable=True),
        sa.Column('change_tag', sa.String(), nullable=True),
        # Utiliser le type ENUM créé ci-dessus
        sa.Column('movement_type', 
                  postgresql.ENUM('CREDIT', 'DEBIT', 'TRANSFER', 'REVERSAL', 'OPERATION', 'TRANSACTION',
                                  name='movement_type_enum', create_type=False),
                  nullable=True),
        sa.Column('load_operations', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('cancel_operations', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('account_roles', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('additional_informations', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('creation_date', sa.DateTime(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), nullable=False),
        sa.Column('deleted', sa.Boolean(), nullable=False),
        sa.Column('status', 
                  postgresql.ENUM('ACTIVE', 'INACTIVE',
                                  name='entity_state', create_type=False),
                  nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('gu_id')
    )
    
    # Créer les index pour movement
    op.create_index('idx_agent_login', 'movement', ['agent_login'], unique=False)
    op.create_index('idx_client_id', 'movement', ['client_id'], unique=False)
    op.create_index('idx_gu_id', 'movement', ['gu_id'], unique=False)
    op.create_index('idx_issuer_account', 'movement', ['issuer_account'], unique=False)
    op.create_index('idx_legal_entity_code', 'movement', ['legal_entity_code'], unique=False)
    op.create_index('idx_merchant_code', 'movement', ['merchant_code'], unique=False)
    op.create_index('idx_partner_dist_id', 'movement', ['partner_dist_id'], unique=False)
    op.create_index('idx_partner_id', 'movement', ['partner_id'], unique=False)
    op.create_index('idx_product_code', 'movement', ['product_code'], unique=False)
    op.create_index('idx_reference_bulk', 'movement', ['reference_bulk'], unique=False)
    op.create_index('idx_service_code', 'movement', ['service_code'], unique=False)
    op.create_index('idx_status_code', 'movement', ['status_code'], unique=False)
    op.create_index('idx_user_login', 'movement', ['user_login'], unique=False)
    op.create_index('index_creation_date', 'movement', ['creation_date'], unique=False)
    
    # Créer la table operation
    op.create_table('operation',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('balance_before', sa.Float(), nullable=True),
        sa.Column('balance_after', sa.Float(), nullable=True),
        sa.Column('account_number', sa.String(), nullable=True),
        sa.Column('account_label', sa.String(), nullable=True),
        sa.Column('super_account_number', sa.String(), nullable=True),
        sa.Column('account_role', sa.String(), nullable=True),
        sa.Column('gu_id', sa.String(), nullable=True),
        sa.Column('id_balance', sa.Integer(), nullable=True),
        # Utiliser le type ENUM créé ci-dessus
        sa.Column('sens_operation',
                  postgresql.ENUM('CREDIT', 'DEBIT', name='operation_direction_enum', create_type=False),
                  nullable=True),
        sa.Column('op_date', sa.DateTime(), nullable=True),
        sa.Column('legal_entity_code', sa.String(), nullable=True),
        sa.Column('product_code', sa.String(), nullable=True),
        sa.Column('global_comission', sa.Float(), nullable=True),
        sa.Column('global_fees', sa.Float(), nullable=True),
        sa.Column('issuer_commissions', sa.Float(), nullable=True),
        sa.Column('acquirer_commissions', sa.Float(), nullable=True),
        sa.Column('issuer_charges', sa.Float(), nullable=True),
        sa.Column('acquirer_charges', sa.Float(), nullable=True),
        sa.Column('impact_rule_code', sa.String(), nullable=True),
        sa.Column('user_login', sa.String(), nullable=True),
        sa.Column('partner_dist_id', sa.String(), nullable=True),
        sa.Column('partner_id', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('amount', 'account_number', 'gu_id', 'impact_rule_code', 
                           name='UniqueAmountAccountNumberGuIDImpactRuleCode')
    )
    
    # Créer les index pour operation
    op.create_index('idx_composite_accountNumber_opDate', 'operation', ['account_number', 'op_date'], unique=False)
    op.create_index('idx_gu_id_op', 'operation', ['gu_id'], unique=False)
    op.create_index('index_account_number', 'operation', ['account_number'], unique=False)
    op.create_index('index_impact_rule_code', 'operation', ['impact_rule_code'], unique=False)
    op.create_index('index_op_date', 'operation', ['op_date'], unique=False)


def downgrade() -> None:
    # Supprimer les tables
    op.drop_index('index_op_date', table_name='operation')
    op.drop_index('index_impact_rule_code', table_name='operation')
    op.drop_index('index_account_number', table_name='operation')
    op.drop_index('idx_gu_id_op', table_name='operation')
    op.drop_index('idx_composite_accountNumber_opDate', table_name='operation')
    op.drop_table('operation')
    
    op.drop_index('index_creation_date', table_name='movement')
    op.drop_index('idx_user_login', table_name='movement')
    op.drop_index('idx_status_code', table_name='movement')
    op.drop_index('idx_service_code', table_name='movement')
    op.drop_index('idx_reference_bulk', table_name='movement')
    op.drop_index('idx_product_code', table_name='movement')
    op.drop_index('idx_partner_id', table_name='movement')
    op.drop_index('idx_partner_dist_id', table_name='movement')
    op.drop_index('idx_merchant_code', table_name='movement')
    op.drop_index('idx_legal_entity_code', table_name='movement')
    op.drop_index('idx_issuer_account', table_name='movement')
    op.drop_index('idx_gu_id', table_name='movement')
    op.drop_index('idx_client_id', table_name='movement')
    op.drop_index('idx_agent_login', table_name='movement')
    op.drop_table('movement')
    
    # Supprimer les types ENUM créés (optionnel)
    from sqlalchemy.dialects.postgresql import ENUM
    
    ENUM(name='operation_direction_enum').drop(op.get_bind(), checkfirst=True)
    ENUM(name='movement_type_enum').drop(op.get_bind(), checkfirst=True)
    # NE PAS supprimer entity_state car il est utilisé par d'autres tables