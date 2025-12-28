-- ============================================================================
-- FUNCTION: impact_accounts_before_operation_insert
-- Updates balance before inserting operation
-- ============================================================================
CREATE OR REPLACE FUNCTION impact_accounts_before_operation_insert(
    p_amount DOUBLE PRECISION,
    p_balance_id INTEGER,
    OUT balance_before DOUBLE PRECISION,
    OUT balance_after DOUBLE PRECISION
)
RETURNS RECORD AS $$
DECLARE
old_balance DOUBLE PRECISION;
BEGIN
    -- Get current balance
SELECT balance INTO old_balance
FROM balance
WHERE id = p_balance_id;

-- Check if balance exists
IF old_balance IS NULL THEN
        RAISE EXCEPTION 'Cannot find balance of ID: %', p_balance_id
            USING ERRCODE = '45001';
END IF;

    -- Update balance
UPDATE balance
SET
    balance = balance + p_amount,
    last_updated_date = NOW(),
    last_updated_amount = p_amount
WHERE id = p_balance_id;

-- Set output parameters
balance_before := old_balance;
    balance_after := old_balance + p_amount;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- TRIGGER FUNCTION: operation_before_insert
-- Automatically updates balance_before and balance_after on operation insert
-- ============================================================================
CREATE OR REPLACE FUNCTION operation_before_insert_trigger()
RETURNS TRIGGER AS $$
DECLARE
result RECORD;
BEGIN
    -- Call the impact function
SELECT * INTO result
FROM impact_accounts_before_operation_insert(
        NEW.amount,
        NEW.id_balance
     );

-- Set balance_before and balance_after
NEW.balance_before := result.balance_before;
    NEW.balance_after := result.balance_after;

RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists and create new one
DROP TRIGGER IF EXISTS operation_before_insert ON operation;

CREATE TRIGGER operation_before_insert
    BEFORE INSERT ON operation
    FOR EACH ROW
    EXECUTE FUNCTION operation_before_insert_trigger();


-- ============================================================================
-- FUNCTION: bulk_insert_operations (JSONB version)
-- Inserts operations from JSON array stored in movement
-- ============================================================================
CREATE OR REPLACE FUNCTION bulk_insert_operations(
    p_movement_id BIGINT,
    load_operations JSONB,
    partner_id VARCHAR
)
RETURNS VOID AS $$
DECLARE
operation JSONB;
BEGIN
    -- Loop through each operation in the JSON array
FOR operation IN SELECT jsonb_array_elements(load_operations)
                            LOOP
                     INSERT INTO operation (
    account_number,
    super_account_number,
    amount,
    balance_after,
    balance_before,
    global_comission,
    global_fees,
    gu_id,
    impact_rule_code,
    legal_entity_code,
    op_date,
    sens_operation,
    product_code,
    id_balance,
    account_role,
    user_login,
    acquirer_commissions,
    acquirer_charges,
    issuer_commissions,
    issuer_charges,
    partner_dist_id,
    partner_id
)
                 VALUES (
                     (operation->>'account_number')::VARCHAR,
                     NULLIF(operation->>'super_account_number', 'null')::VARCHAR,
                     COALESCE((operation->>'amount')::DOUBLE PRECISION, 0),
                     COALESCE((operation->>'balance_after')::DOUBLE PRECISION, 0),
                     COALESCE((operation->>'balance_before')::DOUBLE PRECISION, 0),
                     COALESCE((operation->>'global_commission')::DOUBLE PRECISION, 0),
                     COALESCE((operation->>'global_fees')::DOUBLE PRECISION, 0),
                     COALESCE(operation->>'gu_id', '')::VARCHAR,
                     COALESCE(operation->>'impact_rule_code', '')::VARCHAR,
                     COALESCE(operation->>'legal_entity_code', '')::VARCHAR,
                     NOW(),
                     COALESCE(operation->>'operation_direction', '')::operation_direction_enum,
                     COALESCE(operation->>'product_code', '')::VARCHAR,
                     COALESCE((operation->>'balance_id')::INTEGER, 0),
                     COALESCE(operation->>'account_role', '')::VARCHAR,
                     COALESCE(operation->>'user_login', '')::VARCHAR,
                     COALESCE((operation->>'acquirer_commissions')::DOUBLE PRECISION, 0),
                     COALESCE((operation->>'acquirer_fees')::DOUBLE PRECISION, 0),
                     COALESCE((operation->>'issuer_commissions')::DOUBLE PRECISION, 0),
                     COALESCE((operation->>'issuer_fees')::DOUBLE PRECISION, 0),
                     NULLIF(operation->>'partner_dist_id', 'null')::VARCHAR,
                     partner_id
                     );
END LOOP;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- FUNCTION: bulk_insert_operations (JSON overload)
-- Overload to accept JSON type (converts to JSONB)
-- ============================================================================
CREATE OR REPLACE FUNCTION bulk_insert_operations(
    p_movement_id BIGINT,
    load_operations JSON,
    partner_id VARCHAR
)
RETURNS VOID AS $$
BEGIN
    -- Convert JSON to JSONB and call the main function
    PERFORM bulk_insert_operations(p_movement_id, load_operations::JSONB, partner_id);
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- TRIGGER FUNCTION: movement_status_change
-- Triggers bulk operation insert when movement status changes
-- ============================================================================
CREATE OR REPLACE FUNCTION movement_status_change_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- When status changes to SUCCESSFUL (except from CANCELLATION_REQUEST)
    IF (NEW.status_code = 'SUCCESSFUL' AND
        OLD.status_code NOT IN ('SUCCESSFUL', 'CANCELLATION_REQUEST')) THEN

        -- Insert load operations
        PERFORM bulk_insert_operations(
            NEW.id,
            NEW.load_operations,
            NEW.partner_id
        );
END IF;

    -- When status changes to CANCELLED from CANCELLATION_REQUEST
    IF (NEW.status_code = 'CANCELLED' AND
        OLD.status_code = 'CANCELLATION_REQUEST') THEN

        -- Insert cancel operations
        PERFORM bulk_insert_operations(
            NEW.id,
            NEW.cancel_operations,
            NEW.partner_id
        );
END IF;

RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists and create new one
DROP TRIGGER IF EXISTS movement_status_change ON movement;

CREATE TRIGGER movement_status_change
    BEFORE UPDATE ON movement
    FOR EACH ROW
    WHEN (OLD.status_code IS DISTINCT FROM NEW.status_code)
    EXECUTE FUNCTION movement_status_change_trigger();


-- ============================================================================
-- HELPER FUNCTION: Test bulk_insert_operations
-- For testing purposes
-- ============================================================================
CREATE OR REPLACE FUNCTION test_bulk_insert_operations()
RETURNS TEXT AS $$
DECLARE
test_json JSONB := '[
        {
            "id": null,
            "amount": -100.0,
            "balance_before": null,
            "balance_after": null,
            "account_number": "CISDIST2500000012",
            "account_label": null,
            "super_account_number": null,
            "account_role": "ISSUER",
            "gu_id": "4706a12d-d06c-4434-a032-3e170ef1eec4",
            "balance_id": 3,
            "operation_direction": "DEBIT",
            "op_date": "2025-12-28T20:52:10.925039",
            "legal_entity_code": "INTOUCH_CI",
            "product_code": "TOUCHAPI",
            "global_commission": 1.0,
            "global_fees": -1.0,
            "issuer_commissions": 0.0,
            "acquirer_commissions": 1.0,
            "issuer_fees": -1.0,
            "acquirer_fees": 0.0,
            "impact_rule_code": "NOMINAL_IMPACT",
            "user_login": "701111111",
            "partner_dist_id": null,
            "partner_id": null
        }
    ]'::JSONB;
BEGIN
    PERFORM bulk_insert_operations(1, test_json, NULL);
RETURN 'Test completed successfully';
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- USAGE NOTES
-- ============================================================================
/*

1. To manually call bulk_insert_operations:
   SELECT bulk_insert_operations(
       1,  -- movement_id
       '[{"account_number": "TEST123", "amount": 100.0, ...}]'::JSONB,
       'PARTNER001'
   );

2. The triggers will automatically fire when:
   - An operation is inserted (operation_before_insert)
   - A movement's status is updated (movement_status_change)

3. Key differences from MySQL:
   - Uses JSONB instead of JSON for better performance
   - Uses jsonb_array_elements() instead of recursive CTE
   - Uses ->> operator for JSON text extraction
   - Uses PERFORM instead of CALL for procedures in triggers
   - Uses WHEN clause in trigger for better performance

4. Error handling:
   - PostgreSQL uses RAISE EXCEPTION instead of SIGNAL
   - Custom error codes should be 5 characters

5. Data type mapping:
   - DOUBLE in MySQL → DOUBLE PRECISION in PostgreSQL
   - BIGINT, VARCHAR, INTEGER remain the same

6. IMPORTANT: Enum cast
   - operation_direction is cast to ::operation_direction_enum
   - Make sure your enum values match exactly: 'DEBIT', 'CREDIT', etc.

*/