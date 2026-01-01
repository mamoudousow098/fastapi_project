--
-- PostgreSQL database dump
--

\restrict IninvoHJhhGj0crCGxketB7vIx5myLMCpHYtgGf0Kwjt7NOT6R3BQUabFAu0EnO

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: accountcategory; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.accountcategory AS ENUM (
    'EME',
    'DISTRIBUTOR',
    'CUSTOMER',
    'CORPORATE'
);


ALTER TYPE public.accountcategory OWNER TO postgres;

--
-- Name: accountprefix; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.accountprefix AS ENUM (
    'SUB_ACCOUNT',
    'ACCOUNT'
);


ALTER TYPE public.accountprefix OWNER TO postgres;

--
-- Name: commissionbaseenum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.commissionbaseenum AS ENUM (
    'NOMINAL_AMOUNT',
    'TRANSACTION_AMOUNT',
    'FEES_AMOUNT'
);


ALTER TYPE public.commissionbaseenum OWNER TO postgres;

--
-- Name: constrainttype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.constrainttype AS ENUM (
    'CHECK_PROFILE_HAS_ROLE',
    'CHECK_PENDING_MOVEMENT_AMOUNT',
    'CHECK_ISSUER_OTP',
    'CHECK_NOMBO'
);


ALTER TYPE public.constrainttype OWNER TO postgres;

--
-- Name: entity_state; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.entity_state AS ENUM (
    'ACTIVE',
    'INACTIVE'
);


ALTER TYPE public.entity_state OWNER TO postgres;

--
-- Name: movement_type_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.movement_type_enum AS ENUM (
    'OPERATION',
    'TRANSACTION'
);


ALTER TYPE public.movement_type_enum OWNER TO postgres;

--
-- Name: movementcontext; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.movementcontext AS ENUM (
    'INITIATION',
    'VALIDATION'
);


ALTER TYPE public.movementcontext OWNER TO postgres;

--
-- Name: movementtypeenum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.movementtypeenum AS ENUM (
    'OPERATION',
    'TRANSACTION'
);


ALTER TYPE public.movementtypeenum OWNER TO postgres;

--
-- Name: operation_direction_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.operation_direction_enum AS ENUM (
    'CREDIT',
    'DEBIT'
);


ALTER TYPE public.operation_direction_enum OWNER TO postgres;

--
-- Name: serviceflow; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.serviceflow AS ENUM (
    'ENCAISSEMENT',
    'DECAISSEMENT'
);


ALTER TYPE public.serviceflow OWNER TO postgres;

--
-- Name: servicescope; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.servicescope AS ENUM (
    'INTERNAL',
    'EXTERNAL',
    'PI'
);


ALTER TYPE public.servicescope OWNER TO postgres;

--
-- Name: bulk_insert_operations(bigint, json, character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.bulk_insert_operations(p_movement_id bigint, load_operations json, partner_id character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Convert JSON to JSONB and call the main function
    PERFORM bulk_insert_operations(p_movement_id, load_operations::JSONB, partner_id);
END;
$$;


ALTER FUNCTION public.bulk_insert_operations(p_movement_id bigint, load_operations json, partner_id character varying) OWNER TO postgres;

--
-- Name: bulk_insert_operations(bigint, jsonb, character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.bulk_insert_operations(p_movement_id bigint, load_operations jsonb, partner_id character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.bulk_insert_operations(p_movement_id bigint, load_operations jsonb, partner_id character varying) OWNER TO postgres;

--
-- Name: impact_accounts_before_operation_insert(double precision, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.impact_accounts_before_operation_insert(p_amount double precision, p_balance_id integer, OUT balance_before double precision, OUT balance_after double precision) RETURNS record
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.impact_accounts_before_operation_insert(p_amount double precision, p_balance_id integer, OUT balance_before double precision, OUT balance_after double precision) OWNER TO postgres;

--
-- Name: movement_status_change_trigger(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.movement_status_change_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.movement_status_change_trigger() OWNER TO postgres;

--
-- Name: operation_before_insert_trigger(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.operation_before_insert_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.operation_before_insert_trigger() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: account; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.account (
    id integer NOT NULL,
    account_number character varying,
    phone_number character varying,
    label character varying,
    merchant_code character varying,
    reference_odoo character varying,
    legal_entity_id integer,
    client_id integer,
    bank_id integer,
    country_id character varying,
    category public.accountcategory,
    identification_system character varying,
    identification_number character varying,
    devise character varying,
    overdraft_activated boolean,
    parent_account_id integer,
    balance_id integer,
    kyc_levels character varying[],
    principal_distri_account_number character varying,
    provider_id integer,
    is_blocked boolean NOT NULL,
    is_frozen boolean NOT NULL,
    is_suspended boolean NOT NULL,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL,
    rccm_client_number character varying,
    eme_account_number character varying
);


ALTER TABLE public.account OWNER TO postgres;

--
-- Name: account_account_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.account_account_type (
    id_account integer NOT NULL,
    id_account_type integer NOT NULL
);


ALTER TABLE public.account_account_type OWNER TO postgres;

--
-- Name: account_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.account_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.account_id_seq OWNER TO postgres;

--
-- Name: account_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.account_id_seq OWNED BY public.account.id;


--
-- Name: account_role; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.account_role (
    id integer NOT NULL,
    identifier character varying,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.account_role OWNER TO postgres;

--
-- Name: account_role_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.account_role_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.account_role_id_seq OWNER TO postgres;

--
-- Name: account_role_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.account_role_id_seq OWNED BY public.account_role.id;


--
-- Name: account_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.account_type (
    id integer NOT NULL,
    code character varying,
    label character varying,
    category public.accountcategory,
    prefix public.accountprefix,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.account_type OWNER TO postgres;

--
-- Name: account_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.account_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.account_type_id_seq OWNER TO postgres;

--
-- Name: account_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.account_type_id_seq OWNED BY public.account_type.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: balance; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.balance (
    id integer NOT NULL,
    balance double precision NOT NULL,
    last_updated_date timestamp without time zone,
    last_updated_amount double precision NOT NULL,
    overdraft_amount double precision NOT NULL
);


ALTER TABLE public.balance OWNER TO postgres;

--
-- Name: balance_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.balance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.balance_id_seq OWNER TO postgres;

--
-- Name: balance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.balance_id_seq OWNED BY public.balance.id;


--
-- Name: bank; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bank (
    id integer NOT NULL,
    code character varying,
    name character varying,
    country_iso_code character varying,
    label character varying,
    reference_odoo character varying,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.bank OWNER TO postgres;

--
-- Name: bank_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bank_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bank_id_seq OWNER TO postgres;

--
-- Name: bank_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bank_id_seq OWNED BY public.bank.id;


--
-- Name: client; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client (
    id integer NOT NULL,
    code character varying,
    phone character varying,
    email character varying,
    address character varying,
    notification_url character varying,
    business_area character varying,
    social_reason character varying,
    client_type character varying,
    client_category character varying,
    client_status character varying,
    is_activated boolean NOT NULL,
    is_blocked boolean NOT NULL,
    postal_code character varying,
    photo character varying,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.client OWNER TO postgres;

--
-- Name: client_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.client_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.client_id_seq OWNER TO postgres;

--
-- Name: client_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.client_id_seq OWNED BY public.client.id;


--
-- Name: country; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.country (
    iso_code character varying NOT NULL,
    currency character varying,
    phone_number_length character varying,
    language character varying,
    timezone character varying,
    spoc_number character varying,
    country_name character varying,
    area_code integer,
    currency_number character varying,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.country OWNER TO postgres;

--
-- Name: flow; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.flow (
    id integer NOT NULL,
    label character varying,
    code character varying,
    application_date timestamp without time zone,
    product_code character varying,
    service_code character varying,
    account_number character varying,
    client_category character varying,
    commission_base public.commissionbaseenum NOT NULL,
    version character varying,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.flow OWNER TO postgres;

--
-- Name: flow_constraint; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.flow_constraint (
    id integer NOT NULL,
    code public.constrainttype NOT NULL,
    value character varying,
    flow_id integer,
    service_type_id integer,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL,
    context public.movementcontext NOT NULL
);


ALTER TABLE public.flow_constraint OWNER TO postgres;

--
-- Name: flow_constraint_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.flow_constraint_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.flow_constraint_id_seq OWNER TO postgres;

--
-- Name: flow_constraint_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.flow_constraint_id_seq OWNED BY public.flow_constraint.id;


--
-- Name: flow_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.flow_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.flow_id_seq OWNER TO postgres;

--
-- Name: flow_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.flow_id_seq OWNED BY public.flow.id;


--
-- Name: impact_rule; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.impact_rule (
    id integer NOT NULL,
    code character varying,
    label character varying,
    rule_account_role_id integer,
    impact_rule_type_id integer,
    flow_id integer,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.impact_rule OWNER TO postgres;

--
-- Name: impact_rule_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.impact_rule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.impact_rule_id_seq OWNER TO postgres;

--
-- Name: impact_rule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.impact_rule_id_seq OWNED BY public.impact_rule.id;


--
-- Name: impact_rule_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.impact_rule_type (
    id integer NOT NULL,
    code character varying,
    label character varying,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.impact_rule_type OWNER TO postgres;

--
-- Name: impact_rule_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.impact_rule_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.impact_rule_type_id_seq OWNER TO postgres;

--
-- Name: impact_rule_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.impact_rule_type_id_seq OWNED BY public.impact_rule_type.id;


--
-- Name: interval_rule; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.interval_rule (
    id integer NOT NULL,
    min_amount double precision NOT NULL,
    max_amount double precision NOT NULL,
    percentage double precision,
    fixe double precision,
    impact_rule_id integer NOT NULL
);


ALTER TABLE public.interval_rule OWNER TO postgres;

--
-- Name: interval_rule_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.interval_rule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.interval_rule_id_seq OWNER TO postgres;

--
-- Name: interval_rule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.interval_rule_id_seq OWNED BY public.interval_rule.id;


--
-- Name: legal_entity; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.legal_entity (
    id integer NOT NULL,
    code character varying NOT NULL,
    label character varying NOT NULL,
    address character varying,
    ninea character varying,
    phone_contact character varying,
    email_contact character varying,
    name_contact character varying,
    reference_odoo character varying,
    country_id character varying,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.legal_entity OWNER TO postgres;

--
-- Name: legal_entity_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.legal_entity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.legal_entity_id_seq OWNER TO postgres;

--
-- Name: legal_entity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.legal_entity_id_seq OWNED BY public.legal_entity.id;


--
-- Name: movement; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.movement (
    id integer NOT NULL,
    flow_code character varying,
    flow_version character varying,
    amount double precision,
    impact_date timestamp without time zone,
    sent_date timestamp without time zone,
    cancellation_date timestamp without time zone,
    end_date timestamp without time zone,
    global_commission double precision,
    global_fees double precision,
    issuer_commissions double precision,
    acquirer_commissions double precision,
    issuer_charges double precision,
    acquirer_charges double precision,
    issuer_impact double precision,
    acquirer_impact double precision,
    commission_base double precision,
    charge_base double precision,
    gu_id character varying,
    partner_id character varying,
    partner_dist_id character varying,
    client_id character varying,
    merchant_code character varying,
    legal_entity_code character varying,
    bank_code character varying,
    terminal_id character varying,
    log_id character varying,
    country_iso_code character varying,
    latitude character varying,
    longitude character varying,
    user_login character varying,
    agent_login character varying,
    user_agent character varying,
    product_code character varying,
    service_code character varying,
    service_label character varying,
    service_type_code character varying,
    issuer_account character varying,
    acquirer_account character varying,
    issuer_account_label character varying,
    acquirer_account_label character varying,
    super_issuer character varying,
    super_acquirer character varying,
    status_code character varying,
    message character varying,
    reject_reason character varying,
    cancellation_reason character varying,
    reason character varying,
    reference_bulk character varying,
    slip_number character varying,
    callback_url character varying,
    other_participant_code character varying,
    operator character varying,
    tag character varying,
    change_tag character varying,
    movement_type public.movement_type_enum,
    load_operations jsonb,
    cancel_operations jsonb,
    account_roles jsonb,
    additional_informations jsonb,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.movement OWNER TO postgres;

--
-- Name: movement_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.movement_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.movement_id_seq OWNER TO postgres;

--
-- Name: movement_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.movement_id_seq OWNED BY public.movement.id;


--
-- Name: operation; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.operation (
    id integer NOT NULL,
    amount double precision,
    balance_before double precision,
    balance_after double precision,
    account_number character varying,
    account_label character varying,
    super_account_number character varying,
    account_role character varying,
    gu_id character varying,
    id_balance integer,
    sens_operation public.operation_direction_enum,
    op_date timestamp without time zone,
    legal_entity_code character varying,
    product_code character varying,
    global_comission double precision,
    global_fees double precision,
    issuer_commissions double precision,
    acquirer_commissions double precision,
    issuer_charges double precision,
    acquirer_charges double precision,
    impact_rule_code character varying,
    user_login character varying,
    partner_dist_id character varying,
    partner_id character varying
);


ALTER TABLE public.operation OWNER TO postgres;

--
-- Name: operation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.operation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.operation_id_seq OWNER TO postgres;

--
-- Name: operation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.operation_id_seq OWNED BY public.operation.id;


--
-- Name: operator; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.operator (
    id integer NOT NULL,
    short_code character varying,
    label character varying,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.operator OWNER TO postgres;

--
-- Name: operator_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.operator_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.operator_id_seq OWNER TO postgres;

--
-- Name: operator_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.operator_id_seq OWNED BY public.operator.id;


--
-- Name: product; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product (
    id integer NOT NULL,
    code character varying,
    label character varying,
    kyc_levels character varying[],
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.product OWNER TO postgres;

--
-- Name: product_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.product_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.product_id_seq OWNER TO postgres;

--
-- Name: product_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.product_id_seq OWNED BY public.product.id;


--
-- Name: provider; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.provider (
    id integer NOT NULL,
    code character varying,
    label character varying,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.provider OWNER TO postgres;

--
-- Name: provider_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.provider_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.provider_id_seq OWNER TO postgres;

--
-- Name: provider_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.provider_id_seq OWNED BY public.provider.id;


--
-- Name: rule_account_role; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rule_account_role (
    id integer NOT NULL,
    role_identifier character varying NOT NULL,
    account_types character varying[]
);


ALTER TABLE public.rule_account_role OWNER TO postgres;

--
-- Name: rule_account_role_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.rule_account_role_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rule_account_role_id_seq OWNER TO postgres;

--
-- Name: rule_account_role_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.rule_account_role_id_seq OWNED BY public.rule_account_role.id;


--
-- Name: service; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.service (
    id integer NOT NULL,
    code character varying NOT NULL,
    label character varying NOT NULL,
    service_flow public.serviceflow NOT NULL,
    scope public.servicescope NOT NULL,
    service_type_id integer NOT NULL,
    legal_entity_id integer NOT NULL,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL,
    service_operator_id integer
);


ALTER TABLE public.service OWNER TO postgres;

--
-- Name: service_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.service_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.service_id_seq OWNER TO postgres;

--
-- Name: service_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.service_id_seq OWNED BY public.service.id;


--
-- Name: service_provider; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.service_provider (
    id integer NOT NULL,
    provider_id integer NOT NULL,
    flow_id integer NOT NULL,
    ranking integer,
    url character varying,
    gateway character varying,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.service_provider OWNER TO postgres;

--
-- Name: service_provider_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.service_provider_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.service_provider_id_seq OWNER TO postgres;

--
-- Name: service_provider_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.service_provider_id_seq OWNED BY public.service_provider.id;


--
-- Name: service_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.service_type (
    id integer NOT NULL,
    code character varying NOT NULL,
    short_code character varying,
    label character varying NOT NULL,
    movement_type public.movementtypeenum NOT NULL,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.service_type OWNER TO postgres;

--
-- Name: service_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.service_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.service_type_id_seq OWNER TO postgres;

--
-- Name: service_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.service_type_id_seq OWNED BY public.service_type.id;


--
-- Name: status; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.status (
    id integer NOT NULL,
    code character varying NOT NULL,
    label character varying,
    message text,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.status OWNER TO postgres;

--
-- Name: status_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.status_history (
    id integer NOT NULL,
    status character varying,
    creation_date timestamp without time zone DEFAULT now() NOT NULL,
    message character varying,
    author character varying,
    gu_id character varying
);


ALTER TABLE public.status_history OWNER TO postgres;

--
-- Name: status_history_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.status_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.status_history_id_seq OWNER TO postgres;

--
-- Name: status_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.status_history_id_seq OWNED BY public.status_history.id;


--
-- Name: status_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.status_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.status_id_seq OWNER TO postgres;

--
-- Name: status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.status_id_seq OWNED BY public.status.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    username character varying(100) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    is_active boolean NOT NULL,
    is_superuser boolean NOT NULL,
    creation_date timestamp without time zone NOT NULL,
    updated_date timestamp without time zone NOT NULL,
    deleted boolean NOT NULL,
    status public.entity_state NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: account id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account ALTER COLUMN id SET DEFAULT nextval('public.account_id_seq'::regclass);


--
-- Name: account_role id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account_role ALTER COLUMN id SET DEFAULT nextval('public.account_role_id_seq'::regclass);


--
-- Name: account_type id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account_type ALTER COLUMN id SET DEFAULT nextval('public.account_type_id_seq'::regclass);


--
-- Name: balance id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.balance ALTER COLUMN id SET DEFAULT nextval('public.balance_id_seq'::regclass);


--
-- Name: bank id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bank ALTER COLUMN id SET DEFAULT nextval('public.bank_id_seq'::regclass);


--
-- Name: client id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client ALTER COLUMN id SET DEFAULT nextval('public.client_id_seq'::regclass);


--
-- Name: flow id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.flow ALTER COLUMN id SET DEFAULT nextval('public.flow_id_seq'::regclass);


--
-- Name: flow_constraint id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.flow_constraint ALTER COLUMN id SET DEFAULT nextval('public.flow_constraint_id_seq'::regclass);


--
-- Name: impact_rule id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.impact_rule ALTER COLUMN id SET DEFAULT nextval('public.impact_rule_id_seq'::regclass);


--
-- Name: impact_rule_type id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.impact_rule_type ALTER COLUMN id SET DEFAULT nextval('public.impact_rule_type_id_seq'::regclass);


--
-- Name: interval_rule id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.interval_rule ALTER COLUMN id SET DEFAULT nextval('public.interval_rule_id_seq'::regclass);


--
-- Name: legal_entity id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.legal_entity ALTER COLUMN id SET DEFAULT nextval('public.legal_entity_id_seq'::regclass);


--
-- Name: movement id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movement ALTER COLUMN id SET DEFAULT nextval('public.movement_id_seq'::regclass);


--
-- Name: operation id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.operation ALTER COLUMN id SET DEFAULT nextval('public.operation_id_seq'::regclass);


--
-- Name: operator id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.operator ALTER COLUMN id SET DEFAULT nextval('public.operator_id_seq'::regclass);


--
-- Name: product id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product ALTER COLUMN id SET DEFAULT nextval('public.product_id_seq'::regclass);


--
-- Name: provider id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.provider ALTER COLUMN id SET DEFAULT nextval('public.provider_id_seq'::regclass);


--
-- Name: rule_account_role id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rule_account_role ALTER COLUMN id SET DEFAULT nextval('public.rule_account_role_id_seq'::regclass);


--
-- Name: service id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service ALTER COLUMN id SET DEFAULT nextval('public.service_id_seq'::regclass);


--
-- Name: service_provider id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service_provider ALTER COLUMN id SET DEFAULT nextval('public.service_provider_id_seq'::regclass);


--
-- Name: service_type id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service_type ALTER COLUMN id SET DEFAULT nextval('public.service_type_id_seq'::regclass);


--
-- Name: status id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.status ALTER COLUMN id SET DEFAULT nextval('public.status_id_seq'::regclass);


--
-- Name: status_history id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.status_history ALTER COLUMN id SET DEFAULT nextval('public.status_history_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: account; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.account (id, account_number, phone_number, label, merchant_code, reference_odoo, legal_entity_id, client_id, bank_id, country_id, category, identification_system, identification_number, devise, overdraft_activated, parent_account_id, balance_id, kyc_levels, principal_distri_account_number, provider_id, is_blocked, is_frozen, is_suspended, creation_date, updated_date, deleted, status, rccm_client_number, eme_account_number) FROM stdin;
10	CICDIST2500000010	+2250077868781	LABEL	\N	ODOO GOO	59	1	\N	CI	DISTRIBUTOR	\N	\N	\N	\N	\N	1	\N	\N	\N	f	f	f	2025-02-28 20:39:20	2025-02-28 20:39:20	f	ACTIVE	\N	\N
11	CICDIST2500000011	+2250077868782	LABEL	\N	ODOO GOO	59	1	\N	CI	DISTRIBUTOR	\N	\N	\N	\N	\N	2	\N	\N	\N	f	f	f	2025-02-28 20:41:56	2025-02-28 20:41:56	f	ACTIVE	\N	\N
12	CISDIST2500000012	+2250077868783	LABEL	\N	ODOO GOO	59	\N	\N	CI	DISTRIBUTOR	\N	\N	\N	\N	\N	3	\N	\N	\N	f	f	f	2025-02-28 20:43:01	2025-02-28 20:43:01	f	ACTIVE	\N	\N
13	CISDIST2500000013	+2250077868784	LABEL	\N	ODOO GOO	59	\N	\N	CI	DISTRIBUTOR	\N	\N	\N	\N	\N	4	\N	\N	\N	f	f	f	2025-02-28 20:43:31	2025-03-27 17:47:57	f	ACTIVE	\N	\N
\.


--
-- Data for Name: account_account_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.account_account_type (id_account, id_account_type) FROM stdin;
12	9
13	9
\.


--
-- Data for Name: account_role; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.account_role (id, identifier, creation_date, updated_date, deleted, status) FROM stdin;
1	BANK	2024-12-17 15:44:26	2024-12-17 15:44:26	f	ACTIVE
2	ISSUER	2024-12-17 17:26:04	2024-12-17 17:26:04	f	ACTIVE
3	ACQUIRER	2024-12-17 17:26:08	2024-12-17 17:26:08	f	ACTIVE
4	PROVIDER	2024-12-17 17:26:24	2024-12-17 17:26:24	f	ACTIVE
5	EME	2024-12-17 17:26:30	2024-12-17 17:26:30	f	ACTIVE
6	PRINCIPAL_DISTRIBUTOR	2024-12-17 17:26:36	2024-12-17 17:26:36	f	ACTIVE
7	SUPER_ISSUER	2024-12-17 17:26:43	2024-12-17 17:26:43	f	ACTIVE
8	SUPER_ACQUIRER	2024-12-17 17:26:49	2024-12-17 17:26:49	f	ACTIVE
\.


--
-- Data for Name: account_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.account_type (id, code, label, category, prefix, creation_date, updated_date, deleted, status) FROM stdin;
1	CME_EME	Compte Monnaie Electronique	EME	ACCOUNT	2024-12-02 13:19:09	2024-12-02 13:19:09	f	ACTIVE
2	PI_EME	Compte Fournisseur InterOpérable	EME	ACCOUNT	2024-12-02 13:19:09	2024-12-02 13:19:09	f	ACTIVE
3	CMS_EME	Compte Miroir Sequestre	EME	ACCOUNT	2024-12-02 13:19:09	2024-12-02 13:19:09	f	ACTIVE
4	COM_EME	Compte Opération Miroir	EME	ACCOUNT	2024-12-02 13:19:09	2024-12-02 13:19:09	f	ACTIVE
5	CME_DISTRI	Compte Distributeur Principal TDS	DISTRIBUTOR	ACCOUNT	2024-12-02 13:19:09	2024-12-02 13:19:09	f	ACTIVE
6	MA_DISTRI	Compte Master Agent	DISTRIBUTOR	ACCOUNT	2024-12-02 13:19:09	2024-12-02 13:19:09	f	ACTIVE
7	MD_DISTRI	Compte Marchand Digital	DISTRIBUTOR	SUB_ACCOUNT	2024-12-02 13:19:09	2024-12-02 13:19:09	f	ACTIVE
8	MP_DISTRI	Compte Marchand Physique	DISTRIBUTOR	SUB_ACCOUNT	2024-12-02 13:19:09	2024-12-02 13:19:09	f	ACTIVE
9	SUB_DISTRI	Compte Sous Distributeur	DISTRIBUTOR	SUB_ACCOUNT	2024-12-02 13:19:09	2024-12-02 13:19:09	f	ACTIVE
10	EXT_NOM_DISTRI	Compte Founisseur de Services Hors EME	DISTRIBUTOR	ACCOUNT	2024-12-02 13:19:09	2024-12-02 13:19:09	f	ACTIVE
11	EXT_COM_DISTRI	Compte Commission Founisseur de Services Hors EME	DISTRIBUTOR	ACCOUNT	2024-12-02 13:19:09	2024-12-02 13:19:09	f	ACTIVE
12	ETS_CORP	Compte Client Entreprise	CORPORATE	ACCOUNT	2024-12-02 13:19:09	2024-12-02 13:19:09	f	ACTIVE
13	SUB_CORP	Sous Compte Client Entreprise	CORPORATE	SUB_ACCOUNT	2024-12-02 13:19:09	2024-12-02 13:19:09	f	ACTIVE
14	CUSTOMER	Client final porteur de Wallet	CUSTOMER	ACCOUNT	2024-12-02 13:19:09	2024-12-02 13:19:09	f	ACTIVE
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
99552083ed15
\.


--
-- Data for Name: balance; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.balance (id, balance, last_updated_date, last_updated_amount, overdraft_amount) FROM stdin;
1	0	2025-12-28 16:00:08.419204	0	0
2	0	2025-12-28 17:44:03.975253	0	0
3	399	2025-12-28 21:40:14.563554	-1	0
4	101	2025-12-28 21:40:14.563554	1	0
\.


--
-- Data for Name: bank; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bank (id, code, name, country_iso_code, label, reference_odoo, creation_date, updated_date, deleted, status) FROM stdin;
\.


--
-- Data for Name: client; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client (id, code, phone, email, address, notification_url, business_area, social_reason, client_type, client_category, client_status, is_activated, is_blocked, postal_code, photo, creation_date, updated_date, deleted, status) FROM stdin;
1	CLI-001	+221779999999	john.updated@example.com	456 Updated Street, Dakar	\N	\N	SN	\N	VIP	\N	t	f	\N	\N	2024-05-10 00:00:00	2025-10-21 01:58:30	f	ACTIVE
\.


--
-- Data for Name: country; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.country (iso_code, currency, phone_number_length, language, timezone, spoc_number, country_name, area_code, currency_number, creation_date, updated_date, deleted, status) FROM stdin;
ZW	ZWL	9	ZWD	ZWE	123456789	ZIMBABWE	263	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
BF	XOF	11	FR	GMT	54791977	BURKINA FASO	226	123	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
BJ	XOF	8	BND	BRN	12345678	BENIN	229	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
BW	BWP	7	BWP	BWA	1234567	BOTSWANA	267	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
CD	CD	9	CD	CD	123456789	RÉPUBLIQUE DÉMOCRATIQUE DU CONGO	251	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
CG	CG	9	CG	CG	123456789	CONGO BRAZZAVILLE	251	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
CI	XOF	13	FR	GMT	8819999	COTE D'IVOIRE	225	123	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
CM	XAF	12	FR	GMT	12345678	CAMEROUN	237	123	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
ET	ETB	9	ETB	ETH	123456789	ETHIOPIA	251	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
GA	XAF	12	EN		9999999	GABON	220	123	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
GH	GHS	9	GHC	GHA	123456789	GHANA	233	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
GM	GMD	10	EN		2223333	GAMBIE	220	123	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
GN	GNF	12	FR	GMT	628687094	GUINEE CONAKRY	224	123	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
GW	GW	9	GW	GW	123456789	GUINEE BISSAU	251	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
KE	KES	12	EN		784005005	KENYA	254	123	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
ML	XOF	11	FR	GMT	66252200	MALI	223	123	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
MR	MR	9	MR	MR	123456789	MAURITANIE	251	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
MW	MWK	9	MWK	MWI	123456789	MALAWI	265	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
MZ	MZN	9	MZM	MOZ	12345678	MOZAMBIQUE	258	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
NE	NE	9	NE	NE	123456789	NIGER	251	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
NG	NGN	10	NGN	NGA	8055557755	NIGEIRA	234	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
RCA	RCA	9	RCA	RCA	123456789	REPUBLIQUE CENTRAFRICAINE	251	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
RW	RW	9	RW	RW	123456789	RWANDA	251	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
SN	XOF	12	FR	GMT	766240462	SENEGAL	221	123	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
TD	TD	9	TD	TD	123456789	TCHAD	251	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
TG	XOF	11	FR	GMT	228766240462	TOGO	228	123	2024-12-02 13:18:41	2024-12-02 13:18:41	f	ACTIVE
TZ	TZS	9	TZS	TZA	766698501	TANZANIA	255	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
UG	UGX	9	UGX	UGA	0775673563	UGANDA	256	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
ZA	ZA	9	ZA	Z	123456789	AFRIQUE DU SUD	251	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
ZM	ZMW	9	ZMK	ZMB	123456789	ZAMBIA	260	1	2024-12-02 13:09:25	2024-12-02 13:09:25	f	ACTIVE
\.


--
-- Data for Name: flow; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.flow (id, label, code, application_date, product_code, service_code, account_number, client_category, commission_base, version, creation_date, updated_date, deleted, status) FROM stdin;
2	CI_DPST_INTERNAL	CI_DPS_EME#ALL#ALL#ALL	2025-12-27 16:24:21.706	\N	CI_DPS_EME	\N	\N	NOMINAL_AMOUNT	\N	2025-12-27 17:51:52.106702	2025-12-27 17:51:52.106729	f	ACTIVE
\.


--
-- Data for Name: flow_constraint; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.flow_constraint (id, code, value, flow_id, service_type_id, creation_date, updated_date, deleted, status, context) FROM stdin;
\.


--
-- Data for Name: impact_rule; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.impact_rule (id, code, label, rule_account_role_id, impact_rule_type_id, flow_id, creation_date, updated_date, deleted, status) FROM stdin;
5	NOMINAL_IMPACT	NOMINAL_IMPACT	5	1	2	2025-12-27 17:51:52.122246	2025-12-27 17:51:52.12233	f	ACTIVE
6	NOMINAL_IMPACT	NOMINAL_IMPACT	6	1	2	2025-12-27 17:51:52.122387	2025-12-27 17:51:52.122407	f	ACTIVE
7	CHARGE	CHARGE	7	3	2	2025-12-27 17:51:52.122436	2025-12-27 17:51:52.122445	f	ACTIVE
8	COMMISSION	COMMISSION	8	2	2	2025-12-27 17:51:52.122464	2025-12-27 17:51:52.122472	f	ACTIVE
\.


--
-- Data for Name: impact_rule_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.impact_rule_type (id, code, label, creation_date, updated_date, deleted, status) FROM stdin;
1	NOMINAL_IMPACT	Impact Nominal	2024-12-02 13:19:20	2024-12-02 13:19:20	f	ACTIVE
2	COMMISSION	Commission	2024-12-02 13:19:20	2024-12-02 13:19:20	f	ACTIVE
3	CHARGE	Frais	2024-12-02 13:19:20	2024-12-02 13:19:20	f	ACTIVE
4	CANCELLATION_NOMINAL_IMPACT	Annulation Impact Nominal	2024-12-02 13:19:20	2024-12-02 13:19:20	f	ACTIVE
5	CANCELLATION_COMMISSION	Annulation Commission	2024-12-02 13:19:20	2024-12-02 13:19:20	f	ACTIVE
6	CANCELLATION_CHARGE	Annulation Frais	2024-12-02 13:19:20	2024-12-02 13:19:20	f	ACTIVE
\.


--
-- Data for Name: interval_rule; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.interval_rule (id, min_amount, max_amount, percentage, fixe, impact_rule_id) FROM stdin;
1	0	1000000	-100	0	5
2	0	1000000	100	0	6
3	0	1000000	-1	0	7
4	0	1000000	1	0	8
\.


--
-- Data for Name: legal_entity; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.legal_entity (id, code, label, address, ninea, phone_contact, email_contact, name_contact, reference_odoo, country_id, creation_date, updated_date, deleted, status) FROM stdin;
84	INTOUCH_TG	LABEL	INTOUCH_TG	\N	\N	\N	\N	\N	TG	2024-12-02 13:18:48	2024-12-02 13:18:48	f	ACTIVE
57	Intouch_SA	INTOUCH_SA	SENEGAL	004962579	\N	\N	Intouch SA	\N	SN	2024-12-02 13:12:18	2024-12-02 13:12:18	f	ACTIVE
58	INTOUCH_SN_OLD	Intouch SA	SENEGAL	\N	\N	\N	\N	\N	SN	2024-12-02 13:12:18	2024-12-02 13:12:18	t	ACTIVE
59	INTOUCH_CI	Touch Solutions	COTE D'IVOIRE	\N	\N	\N	\N	\N	CI	2024-12-02 13:12:18	2024-12-02 13:12:18	f	ACTIVE
60	INTOUCH_ML	Intouch Mali SARLU	MALI	\N	\N	\N	\N	\N	ML	2024-12-02 13:12:18	2024-12-02 13:12:18	f	ACTIVE
61	INTOUCH_CM	INTOUCH CAMEROON	CAMEROUN	\N	\N	\N	\N	\N	CM	2024-12-02 13:12:18	2024-12-02 13:12:18	f	ACTIVE
62	INTOUCH_GN	INTOUCH_GN	GUINEE CONAKRY	\N	\N	\N	\N	\N	GN	2024-12-02 13:12:18	2024-12-02 13:12:18	f	ACTIVE
63	INTOUCH_BF	Intouch Burkina SARLu	BURKINA FASO	\N	\N	\N	\N	\N	BF	2024-12-02 13:12:18	2024-12-02 13:12:18	f	ACTIVE
64	INTOUCH_KE	LABEL	KENYA	\N	\N	\N	\N	\N	KE	2024-12-02 13:12:18	2024-12-02 13:12:18	f	ACTIVE
65	INTOUCH_GM	LABEL	GAMBIE	\N	\N	\N	\N	\N	GM	2024-12-02 13:12:19	2024-12-02 13:12:19	f	ACTIVE
66	INTOUCH_GA	LABEL	GABON	\N	\N	\N	\N	\N	GA	2024-12-02 13:12:19	2024-12-02 13:12:19	f	ACTIVE
67	INTOUCH_NG	LABEL	NIGEIRA	\N	\N	\N	\N	\N	NG	2024-12-02 13:12:19	2024-12-02 13:12:19	f	ACTIVE
68	INTOUCH_UG	LABEL	UGANDA	\N	\N	\N	\N	\N	UG	2024-12-02 13:12:19	2024-12-02 13:12:19	f	ACTIVE
69	INTOUCH_MZ	LABEL	MOZAMBIQUE	\N	\N	\N	\N	\N	MZ	2024-12-02 13:12:19	2024-12-02 13:12:19	f	ACTIVE
70	INTOUCH_TZ	LABEL	TANZANIA	\N	\N	\N	\N	\N	TZ	2024-12-02 13:12:19	2024-12-02 13:12:19	f	ACTIVE
71	INTOUCH_BJ	LABEL	BENIN	\N	\N	\N	\N	\N	BJ	2024-12-02 13:12:19	2024-12-02 13:12:19	f	ACTIVE
72	INTOUCH_GH	LABEL	GHANA	\N	\N	\N	\N	\N	GH	2024-12-02 13:12:19	2024-12-02 13:12:19	f	ACTIVE
73	INTOUCH_BW	LABEL	BOTSWANA	\N	\N	\N	\N	\N	BW	2024-12-02 13:12:19	2024-12-02 13:12:19	f	ACTIVE
74	MALAWI	LABEL	INTOUCH_MW	\N	\N	\N	\N	\N	MW	2024-12-02 13:12:19	2024-12-02 13:12:19	f	ACTIVE
75	ZAMBIA	LABEL	INTOUCH_ZM	\N	\N	\N	\N	\N	ZM	2024-12-02 13:12:19	2024-12-02 13:12:19	f	ACTIVE
76	ZIMBABWE	LABEL	INTOUCH_ZW	\N	\N	\N	\N	\N	ZW	2024-12-02 13:12:19	2024-12-02 13:12:19	f	ACTIVE
77	ETHIOPIA	LABEL	INTOUCH_ET	\N	\N	\N	\N	\N	ET	2024-12-02 13:12:20	2024-12-02 13:12:20	f	ACTIVE
78	RWANDA	LABEL	INTOUCH_RW	\N	\N	\N	\N	\N	RW	2024-12-02 13:12:20	2024-12-02 13:12:20	f	ACTIVE
79	CONGO BRAZZAVILLE	LABEL	INTOUCH_CG	\N	\N	\N	\N	\N	CG	2024-12-02 13:12:20	2024-12-02 13:12:20	f	ACTIVE
81	INTOUCH_GW	LABEL	INTOUCH_GW	\N	\N	\N	\N	\N	GW	2024-12-02 13:12:20	2024-12-02 13:12:20	f	ACTIVE
82	MAURITANIE	LABEL	INTOUCH_MR	\N	\N	\N	\N	\N	MR	2024-12-02 13:12:20	2024-12-02 13:12:20	f	ACTIVE
83	INTOUCH_NE	LABEL	INTOUCH_NE	\N	\N	\N	\N	\N	NE	2024-12-02 13:12:20	2024-12-02 13:12:20	f	ACTIVE
\.


--
-- Data for Name: movement; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.movement (id, flow_code, flow_version, amount, impact_date, sent_date, cancellation_date, end_date, global_commission, global_fees, issuer_commissions, acquirer_commissions, issuer_charges, acquirer_charges, issuer_impact, acquirer_impact, commission_base, charge_base, gu_id, partner_id, partner_dist_id, client_id, merchant_code, legal_entity_code, bank_code, terminal_id, log_id, country_iso_code, latitude, longitude, user_login, agent_login, user_agent, product_code, service_code, service_label, service_type_code, issuer_account, acquirer_account, issuer_account_label, acquirer_account_label, super_issuer, super_acquirer, status_code, message, reject_reason, cancellation_reason, reason, reference_bulk, slip_number, callback_url, other_participant_code, operator, tag, change_tag, movement_type, load_operations, cancel_operations, account_roles, additional_informations, creation_date, updated_date, deleted, status) FROM stdin;
1	\N	\N	100000000	\N	\N	\N	\N	0	0	0	0	0	0	0	0	100000000	100000000	1ae9ee4d-2d34-4814-9645-0bec37c346b7	\N	\N	1766865785	\N	INTOUCH_CI	\N	\N	93311100-a05d-47c3-8a80-189e2483955b	\N	\N	\N	701111111	701111111	\N	TOUCHAPI	CI_DPS_ORM	\N	\N	\N	\N	\N	\N	\N	\N	BK_FAILED	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	{"ORIGIN": "LEGACY", "cancel_url": "https://www.google.sn/", "return_url": "https://www.google.sn/", "codeProduit": "API", "destinataire": "777597974", "partner_name": "GU2", "call_back_url": "https://webhook.site/37c12fd5-d9b9-434f-84bf-195f8a7dae21", "original_service_code": "CASHINOMPART", "partner_dist_transaction_id": "TESTN1102_1734084665123"}	2025-12-27 20:03:05.695326	2025-12-27 20:03:05.855628	f	ACTIVE
2	\N	\N	100000000	\N	\N	\N	\N	0	0	0	0	0	0	0	0	100000000	100000000	9d6892dd-7e42-450c-ae83-dac14393820f	\N	\N	1766866457	\N	INTOUCH_CI	\N	\N	ed95a10b-0c46-4966-a96c-1d8a1007444c	\N	\N	\N	701111111	701111111	\N	TOUCHAPI	CI_DPS_ORM	\N	\N	\N	\N	\N	\N	\N	\N	BK_INITIATED	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	{"ORIGIN": "LEGACY", "cancel_url": "https://www.google.sn/", "return_url": "https://www.google.sn/", "codeProduit": "API", "destinataire": "777597974", "partner_name": "GU2", "call_back_url": "https://webhook.site/37c12fd5-d9b9-434f-84bf-195f8a7dae21", "original_service_code": "CASHINOMPART", "partner_dist_transaction_id": "TESTN1102_1734084665123"}	2025-12-27 20:14:17.554082	2025-12-27 20:14:17.554113	f	ACTIVE
3	\N	\N	100000000	\N	\N	\N	\N	0	0	0	0	0	0	0	0	100000000	100000000	1355f0a4-13a1-47d9-883e-0749e8a81ed1	\N	\N	1766867365	\N	INTOUCH_CI	\N	\N	a001270e-9a4a-4d66-93a7-8ba88795eb54	\N	\N	\N	701111111	701111111	\N	TOUCHAPI	CI_DPS_ORM	\N	\N	\N	\N	\N	\N	\N	\N	BK_INITIATED	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	{"ORIGIN": "LEGACY", "cancel_url": "https://www.google.sn/", "return_url": "https://www.google.sn/", "codeProduit": "API", "destinataire": "777597974", "partner_name": "GU2", "call_back_url": "https://webhook.site/37c12fd5-d9b9-434f-84bf-195f8a7dae21", "original_service_code": "CASHINOMPART", "partner_dist_transaction_id": "TESTN1102_1734084665123"}	2025-12-27 20:29:26.251353	2025-12-27 20:29:26.251416	f	ACTIVE
4	\N	\N	100000000	\N	\N	\N	\N	0	0	0	0	0	0	0	0	100000000	100000000	1aeceeb9-dd16-4a9e-a874-8431b96beac1	\N	\N	1766868069	\N	INTOUCH_CI	\N	\N	7cc81a90-d6c0-427a-bfde-c7b28bb334fc	\N	\N	\N	701111111	701111111	\N	TOUCHAPI	CI_DPS_EME	\N	\N	\N	\N	\N	\N	\N	\N	BK_INITIATED	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	{"ORIGIN": "LEGACY", "cancel_url": "https://www.google.sn/", "return_url": "https://www.google.sn/", "codeProduit": "API", "destinataire": "777597974", "partner_name": "GU2", "call_back_url": "https://webhook.site/37c12fd5-d9b9-434f-84bf-195f8a7dae21", "original_service_code": "CASHINOMPART", "partner_dist_transaction_id": "TESTN1102_1734084665123"}	2025-12-27 20:41:09.82627	2025-12-27 20:41:09.826313	f	ACTIVE
5	\N	\N	100000000	\N	\N	\N	\N	0	0	0	0	0	0	0	0	100000000	100000000	e5cda7f4-a164-4fac-bc6d-8326bf88781a	\N	\N	1766868298	\N	INTOUCH_CI	\N	\N	3146bfc5-852e-4a44-b993-5fa5d811d01a	\N	\N	\N	701111111	701111111	\N	TOUCHAPI	CI_DPS_EME	\N	\N	\N	\N	\N	\N	\N	\N	BK_INITIATED	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	{"ORIGIN": "LEGACY", "cancel_url": "https://www.google.sn/", "return_url": "https://www.google.sn/", "codeProduit": "API", "destinataire": "777597974", "partner_name": "GU2", "call_back_url": "https://webhook.site/37c12fd5-d9b9-434f-84bf-195f8a7dae21", "original_service_code": "CASHINOMPART", "partner_dist_transaction_id": "TESTN1102_1734084665123"}	2025-12-27 20:44:58.71843	2025-12-27 20:44:58.718448	f	ACTIVE
6	CI_DPS_EME#ALL#ALL#ALL	\N	100000000	\N	\N	\N	\N	\N	0	\N	\N	0	0	\N	\N	100000000	100000000	4ee1f774-1cf6-4ca5-8229-231b8387334b	\N	\N	\N	\N	INTOUCH_CI	\N	\N	b93ce1d2-9421-4190-b5d4-29a0b893ae54	\N	\N	\N	\N	\N	\N	TOUCHAPI	CI_DPS_EME	\N	\N	\N	\N	\N	\N	\N	\N	BK_INITIATED	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	\N	2025-12-28 10:33:53.188733	2025-12-28 10:33:53.188753	f	ACTIVE
7	CI_DPS_EME#ALL#ALL#ALL	\N	100000000	\N	\N	\N	\N	\N	0	\N	\N	0	0	\N	\N	100000000	100000000	e771d726-3024-4cc2-ac41-c5a300c830bc	\N	\N	\N	\N	INTOUCH_CI	\N	\N	cfd94a1a-a0aa-4362-8ff7-e4652ab31081	\N	\N	\N	\N	\N	\N	TOUCHAPI	CI_DPS_EME	\N	\N	\N	\N	\N	\N	\N	\N	BK_INITIATED	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	\N	2025-12-28 14:03:22.370787	2025-12-28 14:03:22.370821	f	ACTIVE
8	CI_DPS_EME#ALL#ALL#ALL	\N	100000000	\N	\N	\N	\N	\N	0	\N	\N	0	0	\N	\N	100000000	100000000	2e6fa09b-b6f7-4e5a-a987-37e99d940818	\N	\N	\N	\N	INTOUCH_CI	\N	\N	fb686d38-c1d9-471a-8624-7a8846ecb1d4	\N	\N	\N	\N	\N	\N	TOUCHAPI	CI_DPS_EME	\N	\N	\N	\N	\N	\N	\N	\N	BK_INITIATED	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	\N	2025-12-28 14:57:04.994956	2025-12-28 14:57:04.994972	f	ACTIVE
9	CI_DPS_EME#ALL#ALL#ALL	\N	100	\N	\N	\N	\N	\N	-1	\N	\N	-1	0	\N	\N	100	100	57722c0f-43c2-4b0c-8276-e0e4421754cd	\N	\N	\N	\N	INTOUCH_CI	\N	\N	3c47970e-f4ad-42f6-ae4d-3111afee5d66	\N	\N	\N	\N	\N	\N	TOUCHAPI	CI_DPS_EME	\N	\N	\N	\N	\N	\N	\N	\N	BK_INITIATED	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	[{"id": null, "gu_id": "57722c0f-43c2-4b0c-8276-e0e4421754cd", "amount": -100.0, "op_date": "2025-12-28T18:15:47.867255", "balance_id": 3, "partner_id": null, "user_login": null, "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "57722c0f-43c2-4b0c-8276-e0e4421754cd", "amount": 100.0, "op_date": "2025-12-28T18:15:47.872716", "balance_id": 4, "partner_id": null, "user_login": null, "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "57722c0f-43c2-4b0c-8276-e0e4421754cd", "amount": -1.0, "op_date": "2025-12-28T18:15:47.876544", "balance_id": 3, "partner_id": null, "user_login": null, "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "CHARGE", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "57722c0f-43c2-4b0c-8276-e0e4421754cd", "amount": 1.0, "op_date": "2025-12-28T18:15:47.876971", "balance_id": 4, "partner_id": null, "user_login": null, "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "COMMISSION", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}]	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	\N	2025-12-28 18:15:47.878505	2025-12-28 18:15:47.878535	f	ACTIVE
10	CI_DPS_EME#ALL#ALL#ALL	\N	100	\N	\N	\N	\N	\N	-1	\N	\N	-1	0	\N	\N	100	100	89faca21-da2b-49de-8eb1-893471b568a5	\N	\N	1766951809	\N	INTOUCH_CI	\N	\N	ce086853-e9bd-40b2-b3a1-e94de7fedd9f	CI	\N	\N	701111111	701111111	\N	TOUCHAPI	CI_DPS_EME	TouchPoint	DEPOSIT	CISDIST2500000012	CISDIST2500000013	LABEL	LABEL	\N	\N	BK_INITIATED	\N	\N	\N	\N	\N	\N	\N	\N	TPT	\N	\N	TRANSACTION	[{"id": null, "gu_id": "89faca21-da2b-49de-8eb1-893471b568a5", "amount": -100.0, "op_date": "2025-12-28T19:56:49.269131", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "89faca21-da2b-49de-8eb1-893471b568a5", "amount": 100.0, "op_date": "2025-12-28T19:56:49.272510", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "89faca21-da2b-49de-8eb1-893471b568a5", "amount": -1.0, "op_date": "2025-12-28T19:56:49.276042", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "CHARGE", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "89faca21-da2b-49de-8eb1-893471b568a5", "amount": 1.0, "op_date": "2025-12-28T19:56:49.276198", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "COMMISSION", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}]	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	{"ORIGIN": "LEGACY", "cancel_url": "https://www.google.sn/", "return_url": "https://www.google.sn/", "codeProduit": "API", "destinataire": "777597974", "partner_name": "GU2", "call_back_url": "https://webhook.site/37c12fd5-d9b9-434f-84bf-195f8a7dae21", "original_service_code": "CASHINOMPART", "partner_dist_transaction_id": "TESTN1102_1734084665123"}	2025-12-28 19:56:49.277172	2025-12-28 19:56:49.277184	f	ACTIVE
11	CI_DPS_EME#ALL#ALL#ALL	\N	100	\N	\N	\N	\N	\N	-1	\N	\N	-1	0	\N	\N	100	100	11fbe6c7-f3ba-4456-8a6d-53facc4be002	\N	\N	1766952055	\N	INTOUCH_CI	\N	\N	d52a023e-0a1a-41f4-88b7-2a7fabbb05d9	CI	\N	\N	701111111	701111111	\N	TOUCHAPI	CI_DPS_EME	TouchPoint	DEPOSIT	CISDIST2500000012	CISDIST2500000013	LABEL	LABEL	\N	\N	BK_INITIATED	\N	\N	\N	\N	\N	\N	\N	\N	TPT	\N	\N	TRANSACTION	[{"id": null, "gu_id": "11fbe6c7-f3ba-4456-8a6d-53facc4be002", "amount": -100.0, "op_date": "2025-12-28T20:00:55.415816", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "11fbe6c7-f3ba-4456-8a6d-53facc4be002", "amount": 100.0, "op_date": "2025-12-28T20:00:55.426234", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "11fbe6c7-f3ba-4456-8a6d-53facc4be002", "amount": -1.0, "op_date": "2025-12-28T20:00:55.427844", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "CHARGE", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "11fbe6c7-f3ba-4456-8a6d-53facc4be002", "amount": 1.0, "op_date": "2025-12-28T20:00:55.427925", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "COMMISSION", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}]	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	{"ORIGIN": "LEGACY", "cancel_url": "https://www.google.sn/", "return_url": "https://www.google.sn/", "codeProduit": "API", "destinataire": "777597974", "partner_name": "GU2", "call_back_url": "https://webhook.site/37c12fd5-d9b9-434f-84bf-195f8a7dae21", "original_service_code": "CASHINOMPART", "partner_dist_transaction_id": "TESTN1102_1734084665123"}	2025-12-28 20:00:55.428343	2025-12-28 20:00:55.428351	f	ACTIVE
12	CI_DPS_EME#ALL#ALL#ALL	\N	100	\N	\N	\N	2025-12-28 20:28:51.852941	\N	-1	\N	\N	-1	0	\N	\N	100	100	2658b1d4-6f4a-4a19-8996-b76dca95c497	\N	\N	1766953364	\N	INTOUCH_CI	\N	\N	0dfc521d-8d50-48f0-a2b9-4d87e5662fbb	CI	\N	\N	701111111	701111111	\N	TOUCHAPI	CI_DPS_EME	TouchPoint	DEPOSIT	CISDIST2500000012	CISDIST2500000013	LABEL	LABEL	\N	\N	SUCCESSFUL	SUCCESS	\N	\N	\N	\N	\N	\N	\N	TPT	\N	\N	TRANSACTION	[{"id": null, "gu_id": "2658b1d4-6f4a-4a19-8996-b76dca95c497", "amount": -100.0, "op_date": "2025-12-28T20:22:44.952661", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "2658b1d4-6f4a-4a19-8996-b76dca95c497", "amount": 100.0, "op_date": "2025-12-28T20:22:44.957443", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "2658b1d4-6f4a-4a19-8996-b76dca95c497", "amount": -1.0, "op_date": "2025-12-28T20:22:44.961821", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "CHARGE", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "2658b1d4-6f4a-4a19-8996-b76dca95c497", "amount": 1.0, "op_date": "2025-12-28T20:22:44.962258", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "COMMISSION", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}]	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	{"ORIGIN": "LEGACY", "cancel_url": "https://www.google.sn/", "return_url": "https://www.google.sn/", "codeProduit": "API", "destinataire": "777597974", "partner_name": "GU2", "call_back_url": "https://webhook.site/37c12fd5-d9b9-434f-84bf-195f8a7dae21", "original_service_code": "CASHINOMPART", "partner_dist_transaction_id": "TESTN1102_1734084665123"}	2025-12-28 20:22:44.964302	2025-12-28 20:28:51.875824	f	ACTIVE
13	CI_DPS_EME#ALL#ALL#ALL	\N	100	\N	\N	\N	2025-12-28 20:40:30.768389	\N	-1	\N	\N	-1	0	\N	\N	100	100	946bc542-de2e-4cb7-b775-b305de917e30	\N	\N	1766954415	\N	INTOUCH_CI	\N	\N	328e20c5-bee2-4317-8ab6-cb2a4217889c	CI	\N	\N	701111111	701111111	\N	TOUCHAPI	CI_DPS_EME	TouchPoint	DEPOSIT	CISDIST2500000012	CISDIST2500000013	LABEL	LABEL	\N	\N	BK_SUCCESSFUL	SUCCESS	\N	\N	\N	\N	\N	\N	\N	TPT	\N	\N	TRANSACTION	[{"id": null, "gu_id": "946bc542-de2e-4cb7-b775-b305de917e30", "amount": -100.0, "op_date": "2025-12-28T20:40:15.436946", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "946bc542-de2e-4cb7-b775-b305de917e30", "amount": 100.0, "op_date": "2025-12-28T20:40:15.439228", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "946bc542-de2e-4cb7-b775-b305de917e30", "amount": -1.0, "op_date": "2025-12-28T20:40:15.440669", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "CHARGE", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "946bc542-de2e-4cb7-b775-b305de917e30", "amount": 1.0, "op_date": "2025-12-28T20:40:15.443942", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "COMMISSION", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}]	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	{"ORIGIN": "LEGACY", "cancel_url": "https://www.google.sn/", "return_url": "https://www.google.sn/", "codeProduit": "API", "destinataire": "777597974", "partner_name": "GU2", "call_back_url": "https://webhook.site/37c12fd5-d9b9-434f-84bf-195f8a7dae21", "original_service_code": "CASHINOMPART", "partner_dist_transaction_id": "TESTN1102_1734084665123"}	2025-12-28 20:40:15.444792	2025-12-28 20:40:30.770915	f	ACTIVE
14	CI_DPS_EME#ALL#ALL#ALL	\N	100	\N	\N	\N	2025-12-28 20:49:50.002591	\N	-1	\N	\N	-1	0	\N	\N	100	100	1d792985-6d0d-48c6-9e10-265285139c55	\N	\N	1766954969	\N	INTOUCH_CI	\N	\N	3f7e6914-7318-4df7-9103-49727bede195	CI	\N	\N	701111111	701111111	\N	TOUCHAPI	CI_DPS_EME	TouchPoint	DEPOSIT	CISDIST2500000012	CISDIST2500000013	LABEL	LABEL	\N	\N	BK_SUCCESSFUL	SUCCESS	\N	\N	\N	\N	\N	\N	\N	TPT	\N	\N	TRANSACTION	[{"id": null, "gu_id": "1d792985-6d0d-48c6-9e10-265285139c55", "amount": -100.0, "op_date": "2025-12-28T20:49:29.794267", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "1d792985-6d0d-48c6-9e10-265285139c55", "amount": 100.0, "op_date": "2025-12-28T20:49:29.800703", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "1d792985-6d0d-48c6-9e10-265285139c55", "amount": -1.0, "op_date": "2025-12-28T20:49:29.805948", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "CHARGE", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "1d792985-6d0d-48c6-9e10-265285139c55", "amount": 1.0, "op_date": "2025-12-28T20:49:29.806733", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "COMMISSION", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}]	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	{"ORIGIN": "LEGACY", "cancel_url": "https://www.google.sn/", "return_url": "https://www.google.sn/", "codeProduit": "API", "destinataire": "777597974", "partner_name": "GU2", "call_back_url": "https://webhook.site/37c12fd5-d9b9-434f-84bf-195f8a7dae21", "original_service_code": "CASHINOMPART", "partner_dist_transaction_id": "TESTN1102_1734084665123"}	2025-12-28 20:49:29.808569	2025-12-28 20:49:50.005069	f	ACTIVE
15	CI_DPS_EME#ALL#ALL#ALL	\N	100	2025-12-28 20:52:27.009882	\N	\N	2025-12-28 20:52:26.987856	\N	-1	\N	\N	-1	0	\N	\N	100	100	4706a12d-d06c-4434-a032-3e170ef1eec4	\N	\N	1766955130	\N	INTOUCH_CI	\N	\N	b617ebe5-f693-4054-8572-769ebe96952a	CI	\N	\N	701111111	701111111	\N	TOUCHAPI	CI_DPS_EME	TouchPoint	DEPOSIT	CISDIST2500000012	CISDIST2500000013	LABEL	LABEL	\N	\N	SUCCESSFUL	SUCCESS	\N	\N	\N	\N	\N	\N	\N	TPT	\N	\N	TRANSACTION	[{"id": null, "gu_id": "4706a12d-d06c-4434-a032-3e170ef1eec4", "amount": -100.0, "op_date": "2025-12-28T20:52:10.925039", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "4706a12d-d06c-4434-a032-3e170ef1eec4", "amount": 100.0, "op_date": "2025-12-28T20:52:10.929414", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "4706a12d-d06c-4434-a032-3e170ef1eec4", "amount": -1.0, "op_date": "2025-12-28T20:52:10.932763", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "CHARGE", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "4706a12d-d06c-4434-a032-3e170ef1eec4", "amount": 1.0, "op_date": "2025-12-28T20:52:10.933073", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "COMMISSION", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}]	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	{"ORIGIN": "LEGACY", "cancel_url": "https://www.google.sn/", "return_url": "https://www.google.sn/", "codeProduit": "API", "destinataire": "777597974", "partner_name": "GU2", "call_back_url": "https://webhook.site/37c12fd5-d9b9-434f-84bf-195f8a7dae21", "original_service_code": "CASHINOMPART", "partner_dist_transaction_id": "TESTN1102_1734084665123"}	2025-12-28 20:52:10.934484	2025-12-28 20:52:26.991245	f	ACTIVE
16	CI_DPS_EME#ALL#ALL#ALL	\N	100	\N	\N	\N	2025-12-28 21:06:26.945472	\N	-1	\N	\N	-1	0	\N	\N	100	100	021842cc-3a31-4500-9429-e974e4a2a4e0	\N	\N	1766955972	\N	INTOUCH_CI	\N	\N	7eaed907-8272-47ec-b181-85a4777151ec	CI	\N	\N	701111111	701111111	\N	TOUCHAPI	CI_DPS_EME	TouchPoint	DEPOSIT	CISDIST2500000012	CISDIST2500000013	LABEL	LABEL	\N	\N	BK_SUCCESSFUL	SUCCESS	\N	\N	\N	\N	\N	\N	\N	TPT	\N	\N	TRANSACTION	[{"id": null, "gu_id": "021842cc-3a31-4500-9429-e974e4a2a4e0", "amount": -100.0, "op_date": "2025-12-28T21:06:12.482583", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "021842cc-3a31-4500-9429-e974e4a2a4e0", "amount": 100.0, "op_date": "2025-12-28T21:06:12.489578", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "021842cc-3a31-4500-9429-e974e4a2a4e0", "amount": -1.0, "op_date": "2025-12-28T21:06:12.494961", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "CHARGE", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "021842cc-3a31-4500-9429-e974e4a2a4e0", "amount": 1.0, "op_date": "2025-12-28T21:06:12.495318", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "COMMISSION", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}]	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	{"ORIGIN": "LEGACY", "cancel_url": "https://www.google.sn/", "return_url": "https://www.google.sn/", "codeProduit": "API", "destinataire": "777597974", "partner_name": "GU2", "call_back_url": "https://webhook.site/37c12fd5-d9b9-434f-84bf-195f8a7dae21", "original_service_code": "CASHINOMPART", "partner_dist_transaction_id": "TESTN1102_1734084665123"}	2025-12-28 21:06:12.502201	2025-12-28 21:06:26.949163	f	ACTIVE
17	CI_DPS_EME#ALL#ALL#ALL	\N	100	\N	\N	\N	2025-12-28 21:19:09.695816	\N	-1	\N	\N	-1	0	\N	\N	100	100	4c52a327-c3fa-4870-9f4a-f7c3eee5c570	\N	\N	1766956733	\N	INTOUCH_CI	\N	\N	2bd22338-6ec0-4c06-b05f-279e3a42d5cd	CI	\N	\N	701111111	701111111	\N	TOUCHAPI	CI_DPS_EME	TouchPoint	DEPOSIT	CISDIST2500000012	CISDIST2500000013	LABEL	LABEL	\N	\N	BK_SUCCESSFUL	SUCCESS	\N	\N	\N	\N	\N	\N	\N	TPT	\N	\N	TRANSACTION	[{"id": null, "gu_id": "4c52a327-c3fa-4870-9f4a-f7c3eee5c570", "amount": -100.0, "op_date": "2025-12-28T21:18:53.902661", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "4c52a327-c3fa-4870-9f4a-f7c3eee5c570", "amount": 100.0, "op_date": "2025-12-28T21:18:53.906454", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "4c52a327-c3fa-4870-9f4a-f7c3eee5c570", "amount": -1.0, "op_date": "2025-12-28T21:18:53.908761", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "CHARGE", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "4c52a327-c3fa-4870-9f4a-f7c3eee5c570", "amount": 1.0, "op_date": "2025-12-28T21:18:53.908885", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "COMMISSION", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}]	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	{"ORIGIN": "LEGACY", "cancel_url": "https://www.google.sn/", "return_url": "https://www.google.sn/", "codeProduit": "API", "destinataire": "777597974", "partner_name": "GU2", "call_back_url": "https://webhook.site/37c12fd5-d9b9-434f-84bf-195f8a7dae21", "original_service_code": "CASHINOMPART", "partner_dist_transaction_id": "TESTN1102_1734084665123"}	2025-12-28 21:18:53.909519	2025-12-28 21:19:09.700084	f	ACTIVE
18	CI_DPS_EME#ALL#ALL#ALL	\N	100	\N	\N	\N	2025-12-28 21:23:55.038089	\N	-1	\N	\N	-1	0	\N	\N	100	100	99522051-e390-40a8-94a1-643dfdf30f1f	\N	\N	1766957016	\N	INTOUCH_CI	\N	\N	4d3dc85e-ddf4-4000-81e7-17dbe51968fa	CI	\N	\N	701111111	701111111	\N	TOUCHAPI	CI_DPS_EME	TouchPoint	DEPOSIT	CISDIST2500000012	CISDIST2500000013	LABEL	LABEL	\N	\N	BK_SUCCESSFUL	SUCCESS	\N	\N	\N	\N	\N	\N	\N	TPT	\N	\N	TRANSACTION	[{"id": null, "gu_id": "99522051-e390-40a8-94a1-643dfdf30f1f", "amount": -100.0, "op_date": "2025-12-28T21:23:36.548237", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "99522051-e390-40a8-94a1-643dfdf30f1f", "amount": 100.0, "op_date": "2025-12-28T21:23:36.561696", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "99522051-e390-40a8-94a1-643dfdf30f1f", "amount": -1.0, "op_date": "2025-12-28T21:23:36.567689", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "CHARGE", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "99522051-e390-40a8-94a1-643dfdf30f1f", "amount": 1.0, "op_date": "2025-12-28T21:23:36.568182", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "COMMISSION", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}]	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	{"ORIGIN": "LEGACY", "cancel_url": "https://www.google.sn/", "return_url": "https://www.google.sn/", "codeProduit": "API", "destinataire": "777597974", "partner_name": "GU2", "call_back_url": "https://webhook.site/37c12fd5-d9b9-434f-84bf-195f8a7dae21", "original_service_code": "CASHINOMPART", "partner_dist_transaction_id": "TESTN1102_1734084665123"}	2025-12-28 21:23:36.580795	2025-12-28 21:23:55.042186	f	ACTIVE
19	CI_DPS_EME#ALL#ALL#ALL	\N	100	2025-12-28 21:40:14.563554	\N	\N	2025-12-28 21:40:14.5362	\N	-1	\N	\N	-1	0	\N	\N	100	100	1d85b2eb-dc9f-4748-9767-408f1658fde2	\N	\N	1766958013	\N	INTOUCH_CI	\N	\N	4e753805-5c22-4cb0-b7d1-eb324991abf4	CI	\N	\N	701111111	701111111	\N	TOUCHAPI	CI_DPS_EME	TouchPoint	DEPOSIT	CISDIST2500000012	CISDIST2500000013	LABEL	LABEL	\N	\N	SUCCESSFUL	SUCCESS	\N	\N	\N	\N	\N	\N	\N	TPT	\N	\N	TRANSACTION	[{"id": null, "gu_id": "1d85b2eb-dc9f-4748-9767-408f1658fde2", "amount": -100.0, "op_date": "2025-12-28T21:40:14.192927", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "1d85b2eb-dc9f-4748-9767-408f1658fde2", "amount": 100.0, "op_date": "2025-12-28T21:40:14.198136", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "NOMINAL_IMPACT", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "1d85b2eb-dc9f-4748-9767-408f1658fde2", "amount": -1.0, "op_date": "2025-12-28T21:40:14.202397", "balance_id": 3, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ISSUER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000012", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "CHARGE", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "DEBIT", "acquirer_commissions": 1.0, "super_account_number": null}, {"id": null, "gu_id": "1d85b2eb-dc9f-4748-9767-408f1658fde2", "amount": 1.0, "op_date": "2025-12-28T21:40:14.202710", "balance_id": 4, "partner_id": null, "user_login": "701111111", "global_fees": -1.0, "issuer_fees": -1.0, "account_role": "ACQUIRER", "product_code": "TOUCHAPI", "account_label": null, "acquirer_fees": 0.0, "balance_after": null, "account_number": "CISDIST2500000013", "balance_before": null, "partner_dist_id": null, "impact_rule_code": "COMMISSION", "global_commission": 1.0, "legal_entity_code": "INTOUCH_CI", "issuer_commissions": 0.0, "operation_direction": "CREDIT", "acquirer_commissions": 1.0, "super_account_number": null}]	\N	{"ISSUER": "CISDIST2500000012", "ACQUIRER": "CISDIST2500000013"}	{"ORIGIN": "LEGACY", "cancel_url": "https://www.google.sn/", "return_url": "https://www.google.sn/", "codeProduit": "API", "destinataire": "777597974", "partner_name": "GU2", "call_back_url": "https://webhook.site/37c12fd5-d9b9-434f-84bf-195f8a7dae21", "original_service_code": "CASHINOMPART", "partner_dist_transaction_id": "TESTN1102_1734084665123"}	2025-12-28 21:40:14.204258	2025-12-28 21:40:14.543543	f	ACTIVE
\.


--
-- Data for Name: operation; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.operation (id, amount, balance_before, balance_after, account_number, account_label, super_account_number, account_role, gu_id, id_balance, sens_operation, op_date, legal_entity_code, product_code, global_comission, global_fees, issuer_commissions, acquirer_commissions, issuer_charges, acquirer_charges, impact_rule_code, user_login, partner_dist_id, partner_id) FROM stdin;
1	-100	500	400	CISDIST2500000012	\N	\N	ISSUER	1d85b2eb-dc9f-4748-9767-408f1658fde2	3	DEBIT	2025-12-28 21:40:14.563554	INTOUCH_CI	TOUCHAPI	1	-1	0	1	-1	0	NOMINAL_IMPACT	701111111	\N	\N
2	100	0	100	CISDIST2500000013	\N	\N	ACQUIRER	1d85b2eb-dc9f-4748-9767-408f1658fde2	4	CREDIT	2025-12-28 21:40:14.563554	INTOUCH_CI	TOUCHAPI	1	-1	0	1	-1	0	NOMINAL_IMPACT	701111111	\N	\N
3	-1	400	399	CISDIST2500000012	\N	\N	ISSUER	1d85b2eb-dc9f-4748-9767-408f1658fde2	3	DEBIT	2025-12-28 21:40:14.563554	INTOUCH_CI	TOUCHAPI	1	-1	0	1	-1	0	CHARGE	701111111	\N	\N
4	1	100	101	CISDIST2500000013	\N	\N	ACQUIRER	1d85b2eb-dc9f-4748-9767-408f1658fde2	4	CREDIT	2025-12-28 21:40:14.563554	INTOUCH_CI	TOUCHAPI	1	-1	0	1	-1	0	COMMISSION	701111111	\N	\N
\.


--
-- Data for Name: operator; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.operator (id, short_code, label, creation_date, updated_date, deleted, status) FROM stdin;
1	ORM	ORANGE MONEY	2024-12-04 09:50:26	2024-12-04 09:50:26	f	ACTIVE
2	ORG	ORANGE	2024-12-04 09:50:26	2024-12-04 09:50:26	f	ACTIVE
3	FRE	FREE	2024-12-04 09:50:26	2024-12-04 09:50:26	f	ACTIVE
4	EXP	EXPRESSO	2024-12-04 09:50:26	2024-12-04 09:50:26	f	ACTIVE
5	PMB	PROMOBILE	2024-12-04 09:50:26	2024-12-04 09:50:26	f	ACTIVE
6	HYO	HAYO	2024-12-04 09:50:26	2024-12-04 09:50:26	f	ACTIVE
7	WZL	WIZALL	2024-12-04 09:50:26	2024-12-04 09:50:26	f	ACTIVE
8	WVE	WAVE	2024-12-04 09:50:26	2024-12-04 09:50:26	f	ACTIVE
9	MTN	MTN	2024-12-04 09:50:26	2024-12-04 09:50:26	f	ACTIVE
10	MOV	MOOV	2024-12-04 09:50:26	2024-12-04 09:50:26	f	ACTIVE
11	TGC	TOGO COM	2024-12-04 09:50:26	2024-12-04 09:50:26	f	ACTIVE
12	OPE	OPE	2024-12-04 09:50:26	2024-12-04 09:50:26	f	ACTIVE
13	GMD	GRIMALDI	2024-12-04 09:50:27	2024-12-04 09:50:27	f	ACTIVE
14	TPT	TOUCHPOINT	2024-12-04 09:50:27	2024-12-04 09:50:27	f	ACTIVE
15	MLT	MALITEL	2024-12-30 11:31:49	2024-12-30 11:31:49	f	ACTIVE
16	TLC	TELECEL MALI	2024-12-30 12:18:32	2024-12-30 12:18:32	f	ACTIVE
17	TMB	TELMOB Burkina Faso	2024-12-30 15:12:54	2024-12-30 15:12:54	f	ACTIVE
18	CCM	CELLCOM	2025-01-03 15:17:19	2025-01-03 15:17:19	f	ACTIVE
19	ECB	ECOBANK	2025-01-17 09:21:44	2025-01-17 09:21:44	f	ACTIVE
20	SAM	SAMAMONEY	2025-01-17 09:22:08	2025-01-17 09:22:08	f	ACTIVE
21	SUS	MLSUS OMMALI	2025-01-20 09:36:35	2025-01-20 09:36:35	f	ACTIVE
22	BOE	MLBOE	2025-01-20 09:36:50	2025-01-20 09:36:50	f	ACTIVE
23	BAD	MLBAD	2025-01-20 09:37:14	2025-01-20 09:37:14	f	ACTIVE
24	SLD	MLSLD OMMALI	2025-01-20 09:37:30	2025-01-20 09:37:30	f	ACTIVE
25	CGS	MLCGS OMMALI	2025-01-20 09:37:58	2025-01-20 09:37:58	f	ACTIVE
26	BSG	MLBSG OMMALI	2025-01-20 09:38:11	2025-01-20 09:38:11	f	ACTIVE
27	IZI	IZI_OMGN	2025-01-20 09:38:53	2025-01-20 09:38:53	f	ACTIVE
28	BNB	BNB	2025-01-20 09:39:07	2025-01-20 09:39:07	f	ACTIVE
29	ADV	ADVANS	2025-01-20 09:39:31	2025-01-20 09:39:31	f	ACTIVE
30	ORB	ORABANK	2025-01-20 09:40:05	2025-01-20 09:40:05	f	ACTIVE
31	TRM	TRESOR MONEY	2025-01-20 09:40:18	2025-01-20 09:40:18	f	ACTIVE
32	CIE	CIE	2025-01-20 09:40:44	2025-01-20 09:40:44	f	ACTIVE
33	SOD	SODECI	2025-01-20 09:41:13	2025-01-20 09:41:13	f	ACTIVE
34	LDW	LEADWAY	2025-01-20 09:42:03	2025-01-20 09:42:03	f	ACTIVE
35	OPS	OM OPSOL	2025-01-20 09:42:16	2025-01-20 09:42:16	f	ACTIVE
36	FAZ	OM FAAZ	2025-01-20 09:42:42	2025-01-20 09:42:42	f	ACTIVE
37	BFF	OM BFFMS	2025-01-20 09:43:11	2025-01-20 09:43:11	f	ACTIVE
38	YND	YENDA	2025-01-20 09:43:55	2025-01-20 09:43:55	f	ACTIVE
39	OPF	OM PATHFINDER	2025-01-20 09:44:10	2025-01-20 09:44:10	f	ACTIVE
40	ONF	OM NAFA	2025-01-20 09:44:33	2025-01-20 09:44:33	f	ACTIVE
41	POL	OM POLY	2025-01-20 09:44:48	2025-01-20 09:44:48	f	ACTIVE
42	MNF	MOOV NAFA	2025-01-20 09:45:16	2025-01-20 09:45:16	f	ACTIVE
43	SNU	SENEAU	2025-01-20 15:26:18	2025-01-20 15:26:18	f	ACTIVE
44	SNL	SENELEC	2025-01-20 15:26:40	2025-01-20 15:26:40	f	ACTIVE
45	DPW	DPWORLD	2025-01-20 15:26:52	2025-01-20 15:26:52	f	ACTIVE
46	CGL	COGELEC	2025-01-20 15:27:10	2025-01-20 15:27:10	f	ACTIVE
47	WYF	WOYOFAL	2025-01-20 15:27:20	2025-01-20 15:27:20	f	ACTIVE
48	RPD	RAPIDO	2025-01-20 15:27:37	2025-01-20 15:27:37	f	ACTIVE
49	BLR	BOLLORE	2025-01-20 15:28:45	2025-01-20 15:28:45	f	ACTIVE
50	CPS	CAMPUSSEN	2025-01-20 15:29:05	2025-01-20 15:29:05	f	ACTIVE
51	UCD	UCAD	2025-01-20 15:29:14	2025-01-20 15:29:14	f	ACTIVE
52	UVS	UVS	2025-01-20 15:29:29	2025-01-20 15:29:29	f	ACTIVE
53	UGB	UGB	2025-01-20 15:29:40	2025-01-20 15:29:40	f	ACTIVE
54	WTU	WESTERN UNION	2025-01-29 14:23:32	2025-01-29 14:23:32	f	ACTIVE
55	RIA	RIA	2025-01-29 14:23:43	2025-01-29 14:23:43	f	ACTIVE
56	PYC	PAYCARD	2025-02-03 09:27:07	2025-02-03 09:27:07	f	ACTIVE
57	COR	CORIS	2025-02-03 16:19:52	2025-02-03 16:19:52	f	ACTIVE
58	DTN	DTONE	2025-02-14 11:38:12	2025-02-14 11:38:12	f	ACTIVE
59	ARL	AIRALO	2025-02-14 11:38:23	2025-02-14 11:38:23	f	ACTIVE
60	ENG	ENERGIA	2025-02-18 12:01:28	2025-02-18 12:01:28	f	ACTIVE
61	MAN	MANSA	2025-02-19 11:38:21	2025-02-19 11:38:21	f	ACTIVE
\.


--
-- Data for Name: product; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.product (id, code, label, kyc_levels, creation_date, updated_date, deleted, status) FROM stdin;
17	TOUCHWEB	TOUCHWEB	\N	2025-08-06 15:21:29	2025-08-06 15:21:29	f	ACTIVE
1	TOUCHAPI	TOUCHAPI	\N	2024-12-02 13:20:02	2024-12-02 13:20:02	f	ACTIVE
2	TOUCHPAYWEB	TOUCHPAYWEB	\N	2024-12-02 13:20:02	2024-12-02 13:20:02	f	ACTIVE
3	TOUCHPAYAPI	TOUCHPAYAPI	\N	2024-12-02 13:20:02	2024-12-02 13:20:02	f	ACTIVE
4	BULK	BULK	\N	2024-12-02 13:20:02	2024-12-02 13:20:02	f	ACTIVE
5	PDA	PDA	\N	2024-12-02 13:20:02	2024-12-02 13:20:02	f	ACTIVE
6	MYTP	MYTP	\N	2024-12-02 13:20:02	2024-12-02 13:20:02	f	ACTIVE
7	TOUCHPAYPOS	TOUCHPAYPOS	\N	2024-12-02 13:20:02	2024-12-02 13:20:02	f	ACTIVE
8	AGENTAPP	AGENTAPP	\N	2024-12-02 13:20:02	2024-12-02 13:20:02	f	ACTIVE
9	MERCHANTAPP	MERCHANTAPP	\N	2024-12-02 13:20:02	2024-12-02 13:20:02	f	ACTIVE
10	CUSTOMERAPP	CUSTOMERAPP	\N	2024-12-02 13:20:02	2024-12-02 13:20:02	f	ACTIVE
11	BUSINESSAPI	BUSINESSAPI	\N	2024-12-02 13:20:02	2024-12-02 13:20:02	f	ACTIVE
12	BOCORPORATE	BOCORPORATE	\N	2024-12-02 13:20:02	2024-12-02 13:20:02	f	ACTIVE
13	AIO	AIO	\N	2024-12-27 17:04:00	2024-12-27 17:04:00	f	ACTIVE
14	TPT	TPT	\N	2025-05-05 16:57:14	2025-05-05 16:58:11	f	ACTIVE
15	BOM	BOM	\N	2025-05-05 16:57:14	2025-05-05 16:58:11	f	ACTIVE
16	AGENT_API	AGENT_API	\N	2025-07-30 11:20:33	2025-07-30 11:20:33	f	ACTIVE
\.


--
-- Data for Name: provider; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.provider (id, code, label, creation_date, updated_date, deleted, status) FROM stdin;
\.


--
-- Data for Name: rule_account_role; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.rule_account_role (id, role_identifier, account_types) FROM stdin;
5	ISSUER	{SUB_DISTRI}
6	ACQUIRER	{SUB_DISTRI}
7	ISSUER	{SUB_DISTRI}
8	ACQUIRER	{SUB_DISTRI}
\.


--
-- Data for Name: service; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.service (id, code, label, service_flow, scope, service_type_id, legal_entity_id, creation_date, updated_date, deleted, status, service_operator_id) FROM stdin;
1	SN_EMC_EME	Création de monnaie électronique	DECAISSEMENT	INTERNAL	23	57	2024-12-17 17:24:01	2024-12-17 17:24:01	f	ACTIVE	14
2	ML_EMC_EME	Création de monnaie électronique	DECAISSEMENT	INTERNAL	23	60	2024-12-17 18:04:57	2024-12-17 18:04:57	f	ACTIVE	14
3	TG_EMC_EME	Création de monnaie électronique	DECAISSEMENT	INTERNAL	23	84	2024-12-17 20:02:31	2024-12-17 20:02:31	f	ACTIVE	14
4	BF_EMC_EME	Création de monnaie électronique	DECAISSEMENT	INTERNAL	23	63	2024-12-17 20:04:41	2024-12-17 20:04:41	f	ACTIVE	14
5	BJ_EMC_EME	Création de monnaie électronique	DECAISSEMENT	INTERNAL	23	71	2024-12-17 20:06:25	2024-12-17 20:06:25	f	ACTIVE	14
6	CI_EMC_EME	Création de monnaie électronique	DECAISSEMENT	INTERNAL	23	59	2024-12-17 20:08:14	2024-12-17 20:08:14	f	ACTIVE	14
7	GN_EMC_EME	Création de monnaie électronique	DECAISSEMENT	INTERNAL	23	62	2024-12-17 20:11:00	2024-12-17 20:11:00	f	ACTIVE	14
8	NE_EMC_EME	Création de monnaie électronique	DECAISSEMENT	INTERNAL	23	83	2024-12-17 20:37:56	2024-12-17 20:37:56	f	ACTIVE	14
9	GW_EMC_EME	Création de monnaie électronique	DECAISSEMENT	INTERNAL	23	81	2024-12-17 20:40:27	2024-12-17 20:40:27	f	ACTIVE	14
10	NE_BLM_EME	Migration de solde sous distri	DECAISSEMENT	INTERNAL	24	83	2024-12-18 09:02:18	2024-12-18 09:02:18	f	ACTIVE	14
11	SN_BLM_EME	Migration de solde sous distri	DECAISSEMENT	INTERNAL	24	57	2024-12-18 09:03:56	2024-12-18 09:03:56	f	ACTIVE	14
12	GN_BLM_EME	Migration de solde sous distri	DECAISSEMENT	INTERNAL	24	62	2024-12-18 09:46:18	2024-12-18 09:46:18	f	ACTIVE	14
13	GW_BLM_EME	Migration de solde sous distri	DECAISSEMENT	INTERNAL	24	81	2024-12-18 09:48:12	2024-12-18 09:48:12	f	ACTIVE	14
14	ML_BLM_EME	Migration de solde sous distri	DECAISSEMENT	INTERNAL	24	60	2024-12-18 09:50:07	2024-12-18 09:50:07	f	ACTIVE	14
15	TG_BLM_EME	Migration de solde sous distri	DECAISSEMENT	INTERNAL	24	84	2024-12-18 09:55:24	2024-12-18 09:55:24	f	ACTIVE	14
16	BF_BLM_EME	Migration de solde sous distri	DECAISSEMENT	INTERNAL	24	63	2024-12-18 09:56:58	2024-12-18 09:56:58	f	ACTIVE	14
17	BJ_BLM_EME	Migration de solde sous distri	DECAISSEMENT	INTERNAL	24	71	2024-12-18 09:58:39	2024-12-18 09:58:39	f	ACTIVE	14
18	CI_BLM_EME	Migration de solde sous distri	DECAISSEMENT	INTERNAL	24	59	2024-12-18 10:00:16	2024-12-18 10:00:16	f	ACTIVE	14
19	SN_CCT_EME	Transfert Touchpoint	ENCAISSEMENT	INTERNAL	3	57	2024-12-19 15:58:20	2024-12-19 15:58:20	f	ACTIVE	14
20	SN_BTU_EME	Approvisionnement Compte Banque	DECAISSEMENT	INTERNAL	25	57	2024-12-20 13:15:01	2024-12-20 13:15:01	f	ACTIVE	14
21	GN_BTU_EME	Approvisionnement Compte Banque	DECAISSEMENT	INTERNAL	25	62	2024-12-20 13:26:49	2024-12-20 13:26:49	f	ACTIVE	14
22	ML_BTU_EME	Approvisionnement Compte Banque	DECAISSEMENT	INTERNAL	25	60	2024-12-20 13:38:29	2024-12-20 13:38:29	f	ACTIVE	14
23	BJ_BTU_EME	Approvisionnement Compte Banque	DECAISSEMENT	INTERNAL	25	71	2024-12-20 13:40:24	2024-12-20 13:40:24	f	ACTIVE	14
24	TG_BTU_EME	Approvisionnement Compte Banque	DECAISSEMENT	INTERNAL	25	84	2024-12-20 13:43:06	2024-12-20 13:43:06	f	ACTIVE	14
25	GW_BTU_EME	Approvisionnement Compte Banque	DECAISSEMENT	INTERNAL	25	81	2024-12-20 13:43:11	2024-12-20 13:43:11	f	ACTIVE	14
26	NE_BTU_EME	Approvisionnement Compte Banque	DECAISSEMENT	INTERNAL	25	83	2024-12-20 13:47:55	2024-12-20 13:47:55	f	ACTIVE	14
27	BF_BTU_EME	Approvisionnement Compte Banque	DECAISSEMENT	INTERNAL	25	63	2024-12-20 13:49:54	2024-12-20 13:49:54	f	ACTIVE	14
28	CI_BTU_EME	Approvisionnement Compte Banque	DECAISSEMENT	INTERNAL	25	59	2024-12-20 13:54:15	2024-12-20 13:54:15	f	ACTIVE	14
29	BJ_DPS_MOV	DEPOT MOOV BEN	ENCAISSEMENT	EXTERNAL	1	71	2024-12-23 10:59:11	2024-12-23 10:59:11	f	ACTIVE	10
30	BJ_DPS_MTN	DEPOT MTN BEN	ENCAISSEMENT	EXTERNAL	1	71	2024-12-23 11:00:30	2024-12-23 11:00:30	f	ACTIVE	9
31	BJ_MPM_MOV	PAYMENT MOOV BEN	DECAISSEMENT	EXTERNAL	8	71	2024-12-23 11:02:40	2024-12-23 11:02:40	f	ACTIVE	10
32	BJ_MPM_MTN	PAIEMENT MTN BEN	DECAISSEMENT	EXTERNAL	8	71	2024-12-23 11:03:51	2024-12-23 11:03:51	f	ACTIVE	9
33	TG_DPS_MOV	DEPOT MOOV TG	ENCAISSEMENT	EXTERNAL	1	84	2024-12-23 11:08:35	2024-12-23 11:08:35	f	ACTIVE	10
34	TG_DPS_TGC	DEPOT TMONEY TG	ENCAISSEMENT	EXTERNAL	1	84	2024-12-23 11:09:57	2024-12-23 11:09:57	f	ACTIVE	11
35	TG_MPM_MOV	PAYMENT MOOV TG	DECAISSEMENT	EXTERNAL	8	84	2024-12-23 11:11:36	2024-12-23 11:11:36	f	ACTIVE	10
36	TG_MPM_TGC	PAYMENT TMONEY TG	DECAISSEMENT	EXTERNAL	8	84	2024-12-23 11:14:46	2024-12-23 11:14:46	f	ACTIVE	11
37	SN_DPS_FRE	Mixx By Yas	ENCAISSEMENT	EXTERNAL	1	57	2024-12-23 12:04:20	2024-12-23 12:04:20	f	ACTIVE	3
38	SN_DPS_ORM	Orange Money	ENCAISSEMENT	EXTERNAL	1	57	2024-12-23 12:05:50	2024-12-23 12:05:50	f	ACTIVE	1
39	SN_DPS_WVE	Wave	ENCAISSEMENT	EXTERNAL	1	57	2024-12-23 12:07:22	2024-12-23 12:07:22	f	ACTIVE	8
40	SN_MPM_FRE	Mixx By Yas	DECAISSEMENT	EXTERNAL	8	57	2024-12-23 12:08:25	2024-12-23 12:08:25	f	ACTIVE	3
41	SN_MPM_ORM_OTP	Orange Money	DECAISSEMENT	EXTERNAL	8	57	2024-12-23 12:09:25	2024-12-23 12:09:25	f	ACTIVE	1
42	SN_MPM_ORM_QR	Max it	DECAISSEMENT	EXTERNAL	8	57	2024-12-23 12:10:24	2024-12-23 12:10:24	f	ACTIVE	1
43	SN_MPM_WVE	Wave	DECAISSEMENT	EXTERNAL	8	57	2024-12-23 12:11:33	2024-12-23 12:11:33	f	ACTIVE	8
44	SN_WDW_TPT	Retrait Touchpoint	DECAISSEMENT	EXTERNAL	2	57	2024-12-23 12:28:53	2024-12-23 12:28:53	f	ACTIVE	14
45	SN_DPS_TPT	TouchPoint	ENCAISSEMENT	EXTERNAL	1	57	2024-12-23 12:29:59	2024-12-23 12:29:59	f	ACTIVE	14
46	CI_DPS_MOV	Moov Money	ENCAISSEMENT	EXTERNAL	1	59	2024-12-23 14:26:26	2024-12-23 14:26:26	f	ACTIVE	10
47	CI_DPS_MTN	MTN	ENCAISSEMENT	EXTERNAL	1	59	2024-12-23 14:27:55	2024-12-23 14:27:55	f	ACTIVE	9
48	CI_DPS_WVE	Wave	ENCAISSEMENT	EXTERNAL	1	59	2024-12-23 14:32:32	2024-12-23 14:32:32	f	ACTIVE	8
49	CI_MPM_WVE	Wave	DECAISSEMENT	EXTERNAL	8	59	2024-12-23 14:35:46	2024-12-23 14:35:46	f	ACTIVE	8
50	CI_MPM_MOV	Moov Money	DECAISSEMENT	EXTERNAL	8	59	2024-12-23 15:24:31	2024-12-23 15:24:31	f	ACTIVE	10
51	CI_MPM_ORM	Orange Money	DECAISSEMENT	EXTERNAL	8	59	2024-12-23 15:25:58	2024-12-23 15:25:58	f	ACTIVE	1
52	CI_MPM_MTN	MTN	DECAISSEMENT	EXTERNAL	8	59	2024-12-23 15:27:34	2024-12-23 15:27:34	f	ACTIVE	9
53	GN_MPM_ORM	PAIEMENT MARCHAND OM GN	DECAISSEMENT	EXTERNAL	8	62	2024-12-24 12:23:39	2024-12-24 12:23:39	f	ACTIVE	1
54	GN_WDW_MTN	Retrait MTN	DECAISSEMENT	EXTERNAL	2	62	2024-12-24 12:48:34	2025-02-03 18:00:09	f	ACTIVE	9
55	ML_MPM_ORG	PAIEMENT MARCHAND ORANGE MONEY ML	DECAISSEMENT	EXTERNAL	8	60	2024-12-24 12:59:17	2024-12-24 12:59:17	f	ACTIVE	2
56	ML_MPM_MOV	PAIEMENT MARCHAND MOOV ML	DECAISSEMENT	EXTERNAL	8	60	2024-12-24 13:02:04	2024-12-24 13:02:04	f	ACTIVE	10
57	SN_MPM_EME	TouchPoint	DECAISSEMENT	INTERNAL	8	57	2024-12-24 13:28:36	2024-12-24 13:28:36	f	ACTIVE	14
58	SN_DPS_EME	TouchPoint	ENCAISSEMENT	INTERNAL	1	57	2024-12-24 13:34:03	2024-12-24 13:34:03	f	ACTIVE	14
59	GA_DPS_TPT	Transfert Touchpoint GA	ENCAISSEMENT	EXTERNAL	1	66	2024-12-24 15:54:52	2024-12-24 15:54:52	f	ACTIVE	14
60	CI_DPS_TPT	Envoi Touchpoint cc CI	ENCAISSEMENT	EXTERNAL	1	59	2024-12-24 16:01:49	2024-12-24 16:01:49	f	ACTIVE	14
61	CI_WDW_TPT	Retrait Touchpoint cc CI	DECAISSEMENT	EXTERNAL	2	59	2024-12-24 16:14:16	2024-12-24 16:14:16	f	ACTIVE	14
62	GN_MPM_MTN	PAIEMENT MARCHAND MTN GN	DECAISSEMENT	EXTERNAL	8	62	2024-12-26 10:29:42	2024-12-26 10:29:42	f	ACTIVE	9
63	SN_DPS_TPT_CC	Transfert Touchpoint cc	ENCAISSEMENT	EXTERNAL	1	57	2024-12-26 13:14:11	2024-12-26 13:14:11	f	ACTIVE	14
64	SN_WDW_TPT_CC	Retrait Touchpoint cc	DECAISSEMENT	EXTERNAL	2	57	2024-12-26 13:15:24	2024-12-26 13:15:24	f	ACTIVE	14
65	SN_DPS_TPT_CB	Transfert Touchpoint CB SN	ENCAISSEMENT	EXTERNAL	1	57	2024-12-26 13:16:35	2024-12-26 13:16:35	f	ACTIVE	14
66	SN_WDW_TPT_CB	Retrait Touchpoint SN CB	DECAISSEMENT	EXTERNAL	2	57	2024-12-26 13:18:43	2024-12-26 13:18:43	f	ACTIVE	14
67	CI_DPS_TPT_CC	Envoi Touchpoint cc CI	ENCAISSEMENT	EXTERNAL	1	59	2024-12-26 13:29:59	2024-12-26 13:29:59	f	ACTIVE	14
68	CI_DPS_TPT_CB	Transfert Touchpoint CB CI	ENCAISSEMENT	EXTERNAL	1	59	2024-12-26 13:32:09	2024-12-26 13:32:09	f	ACTIVE	14
69	CI_WDW_TPT_CC	Retrait Touchpoint cc CI	DECAISSEMENT	EXTERNAL	2	59	2024-12-26 13:39:46	2024-12-26 13:39:46	f	ACTIVE	14
70	CI_WDW_TPT_CB	Retrait Touchpoint CI CB	DECAISSEMENT	EXTERNAL	2	59	2024-12-26 13:41:09	2024-12-26 13:41:09	f	ACTIVE	14
71	SN_ATM_ORG	Orange	ENCAISSEMENT	EXTERNAL	7	57	2024-12-26 16:00:08	2024-12-26 16:00:08	f	ACTIVE	2
72	GN_DPS_ORM	DEPOT ORANGE MONEY GN	ENCAISSEMENT	EXTERNAL	1	62	2024-12-26 16:00:59	2024-12-26 16:00:59	f	ACTIVE	1
73	GN_DPS_MTN	DEPOT MTN GN	ENCAISSEMENT	EXTERNAL	1	62	2024-12-26 16:02:30	2024-12-26 16:02:30	f	ACTIVE	9
74	BF_DPS_MOV	DEPOT MOBICASH BF	ENCAISSEMENT	EXTERNAL	1	63	2024-12-26 16:06:07	2024-12-26 16:06:07	f	ACTIVE	10
75	BF_DPS_ORM	DEPOT OM BF	ENCAISSEMENT	EXTERNAL	1	63	2024-12-26 16:07:15	2024-12-26 16:07:15	f	ACTIVE	1
76	BF_MPM_ORM	PAIEMENT MARCHAND OM BF	DECAISSEMENT	EXTERNAL	8	63	2024-12-26 16:08:23	2024-12-26 16:08:23	f	ACTIVE	1
77	BF_MPM_MOV	PAIEMENT MARCHAND MOOV BF	DECAISSEMENT	EXTERNAL	8	63	2024-12-26 16:09:12	2024-12-26 16:09:12	f	ACTIVE	10
78	ML_DPS_MOV	DEPOT MOOV ML	ENCAISSEMENT	EXTERNAL	1	60	2024-12-26 16:43:41	2024-12-26 16:43:41	f	ACTIVE	10
79	ML_DPS_ORM	DEPOT OM ML	ENCAISSEMENT	EXTERNAL	1	60	2024-12-26 16:59:32	2024-12-26 16:59:32	f	ACTIVE	1
80	SN_ATM_PMB	Promobile	ENCAISSEMENT	EXTERNAL	7	57	2024-12-26 18:07:32	2024-12-26 18:07:32	f	ACTIVE	5
81	SN_ATM_EXP	Expresso	ENCAISSEMENT	EXTERNAL	7	57	2024-12-30 11:16:54	2024-12-30 11:16:54	f	ACTIVE	4
82	SN_ATM_FRE	Yas	ENCAISSEMENT	EXTERNAL	7	57	2024-12-30 11:24:33	2024-12-30 11:24:33	f	ACTIVE	3
83	CI_ATM_ORG	Orange	ENCAISSEMENT	EXTERNAL	7	59	2024-12-30 11:35:31	2024-12-30 11:35:31	f	ACTIVE	2
84	CI_ATM_MOV	Moov	ENCAISSEMENT	EXTERNAL	7	59	2024-12-30 11:36:38	2024-12-30 11:36:38	f	ACTIVE	10
85	CI_ATM_MTN	MTN	ENCAISSEMENT	EXTERNAL	7	59	2024-12-30 11:37:33	2024-12-30 11:37:33	f	ACTIVE	9
86	CI_CCT_EME	Transfert Touchpoint	ENCAISSEMENT	INTERNAL	3	59	2024-12-30 12:57:49	2024-12-30 12:57:49	f	ACTIVE	14
87	CI_MPM_EME	Touchpoint	DECAISSEMENT	INTERNAL	8	59	2024-12-30 13:06:28	2024-12-30 13:06:28	f	ACTIVE	14
88	CI_DPS_ORM	Orange Money	ENCAISSEMENT	EXTERNAL	1	59	2024-12-30 13:13:06	2024-12-30 13:13:06	f	ACTIVE	1
89	CI_MPM_ORM_OTP	Orange Money	DECAISSEMENT	EXTERNAL	8	59	2024-12-30 13:23:41	2024-12-30 13:23:41	f	ACTIVE	1
90	ML_MPM_EME	Paiement Touchpoint	DECAISSEMENT	INTERNAL	8	60	2024-12-30 13:30:33	2024-12-30 13:30:33	f	ACTIVE	14
91	ML_CCT_EME	Transfert Touchpoint	ENCAISSEMENT	INTERNAL	3	60	2024-12-30 13:31:52	2024-12-30 13:31:52	f	ACTIVE	14
92	ML_ATM_MLT	AIRTIME MALITEL ML	ENCAISSEMENT	EXTERNAL	7	60	2024-12-30 15:13:08	2024-12-30 15:13:08	f	ACTIVE	15
93	ML_ATM_ORG	AIRTIME ORANGE ML	ENCAISSEMENT	EXTERNAL	7	60	2024-12-30 15:14:00	2024-12-30 15:14:00	f	ACTIVE	2
94	ML_ATM_TLC	AIRTIME TELECEL ML	ENCAISSEMENT	EXTERNAL	7	60	2024-12-30 15:21:27	2024-12-30 15:21:27	f	ACTIVE	16
95	BJ_MPM_EME	Paiement Touchpoint	DECAISSEMENT	INTERNAL	8	71	2024-12-30 15:49:34	2024-12-30 15:49:34	f	ACTIVE	14
96	BJ_CCT_EME	Transfert Touchpoint	ENCAISSEMENT	INTERNAL	3	71	2024-12-30 17:01:22	2024-12-30 17:01:22	f	ACTIVE	14
97	TG_MPM_EME	Paiement Touchpoint	DECAISSEMENT	INTERNAL	8	84	2024-12-30 17:08:10	2024-12-30 17:08:10	f	ACTIVE	14
98	TG_CCT_EME	Transfert Touchpoint	ENCAISSEMENT	INTERNAL	3	84	2024-12-31 09:40:32	2024-12-31 09:40:32	f	ACTIVE	14
99	BF_ATM_TLC	AIRTIME TELECEL BF	ENCAISSEMENT	EXTERNAL	7	63	2024-12-31 15:38:24	2024-12-31 15:38:24	f	ACTIVE	16
100	BF_ATM_ORG	AIRTIME ORANGE BF	ENCAISSEMENT	EXTERNAL	7	63	2024-12-31 15:39:39	2024-12-31 15:39:39	f	ACTIVE	2
101	BF_ATM_TMB	AIRTIME TELMOB BF	ENCAISSEMENT	EXTERNAL	7	63	2025-01-03 14:45:57	2025-01-03 14:45:57	f	ACTIVE	17
102	GN_ATM_ORG	AIRTIME ORANGE GN	ENCAISSEMENT	EXTERNAL	7	62	2025-01-03 14:47:38	2025-01-03 14:47:38	f	ACTIVE	2
103	GN_ATM_MTN	AIRTIME MTN GN	ENCAISSEMENT	EXTERNAL	7	62	2025-01-03 14:50:26	2025-01-03 14:50:26	f	ACTIVE	9
104	GN_ATM_CCM	AIRTIME CELLCOM GN	ENCAISSEMENT	EXTERNAL	7	62	2025-01-03 15:20:11	2025-01-03 15:20:11	f	ACTIVE	18
105	ML_WDW_MOV	CASHOUT MOOV ML	DECAISSEMENT	EXTERNAL	2	60	2025-01-06 15:37:11	2025-01-06 15:37:11	f	ACTIVE	10
106	ML_WDW_ORM	CASHOUT OM ML	DECAISSEMENT	EXTERNAL	2	60	2025-01-06 15:38:25	2025-01-06 15:38:25	f	ACTIVE	1
107	CI_DPS_EME	TouchPoint	ENCAISSEMENT	INTERNAL	1	59	2025-01-10 13:31:56	2025-01-10 13:31:56	f	ACTIVE	14
108	SN_CCP_EME	COMPENSE CORPORATE	ENCAISSEMENT	INTERNAL	12	57	2025-01-13 15:29:48	2025-01-13 15:29:48	f	ACTIVE	14
109	SN_CTU_EME	APPRO CORPORATE	ENCAISSEMENT	INTERNAL	11	57	2025-01-13 15:30:30	2025-01-13 15:30:30	f	ACTIVE	14
110	SN_MAT_EME	Transfert compte à sous compte	DECAISSEMENT	INTERNAL	6	57	2025-01-13 15:33:20	2025-01-13 15:33:20	f	ACTIVE	14
111	SN_AAT_EME	Transfert UV sous compte à sous compte	DECAISSEMENT	INTERNAL	4	57	2025-01-13 16:00:09	2025-01-13 16:00:09	f	ACTIVE	14
112	SN_EMT_EME	Transformation d'UV Orange Money	ENCAISSEMENT	INTERNAL	21	57	2025-01-13 16:38:12	2025-01-13 16:38:12	f	ACTIVE	1
113	SN_UVT_EME	Transformation d'UV Agence Orange Money	DECAISSEMENT	INTERNAL	22	57	2025-01-13 16:41:50	2025-01-13 16:41:50	f	ACTIVE	1
114	CI_WDW_MTN	CASHOUT MTN CI	DECAISSEMENT	EXTERNAL	2	59	2025-01-15 10:08:40	2025-01-15 10:08:40	f	ACTIVE	9
115	SN_MPM_ORM	Orange Money	DECAISSEMENT	EXTERNAL	8	57	2025-01-20 18:28:25	2025-01-20 18:28:25	f	ACTIVE	1
116	SN_TTU_EME	Approvisionnement Compte TDS	DECAISSEMENT	INTERNAL	26	57	2025-01-21 10:48:53	2025-01-21 10:48:53	f	ACTIVE	14
117	GN_DPS_TPT	DEPOT TP GN	ENCAISSEMENT	EXTERNAL	1	62	2025-01-21 12:20:29	2025-01-21 12:20:29	f	ACTIVE	14
118	GW_TTU_EME	Approvisionnement Compte TDS	DECAISSEMENT	INTERNAL	26	81	2025-01-21 12:31:55	2025-01-21 12:31:55	f	ACTIVE	14
119	TG_TTU_EME	Approvisionnement Compte TDS	DECAISSEMENT	INTERNAL	26	84	2025-01-21 12:34:25	2025-01-21 12:34:25	f	ACTIVE	14
120	ML_TTU_EME	Approvisionnement Compte TDS	DECAISSEMENT	INTERNAL	26	60	2025-01-21 12:37:29	2025-01-21 12:37:29	f	ACTIVE	14
121	NE_TTU_EME	Approvisionnement Compte TDS	DECAISSEMENT	INTERNAL	26	83	2025-01-21 12:39:38	2025-01-21 12:39:38	f	ACTIVE	14
122	GN_TTU_EME	Approvisionnement Compte TDS	DECAISSEMENT	INTERNAL	26	62	2025-01-21 12:42:52	2025-01-21 12:42:52	f	ACTIVE	14
123	ML_ATM_WVE	AIRTIME MALITEL WAVE ML	ENCAISSEMENT	EXTERNAL	7	60	2025-01-21 12:43:58	2025-01-21 12:43:58	f	ACTIVE	8
124	CI_TTU_EME	Approvisionnement Compte TDS	DECAISSEMENT	INTERNAL	26	59	2025-01-21 12:45:16	2025-01-21 12:45:16	f	ACTIVE	14
125	BF_TTU_EME	Approvisionnement Compte TDS	DECAISSEMENT	INTERNAL	26	63	2025-01-21 12:49:30	2025-01-21 12:49:30	f	ACTIVE	14
126	BJ_TTU_EME	Approvisionnement Compte TDS	DECAISSEMENT	INTERNAL	26	71	2025-01-21 12:52:39	2025-01-21 12:52:39	f	ACTIVE	14
127	CI_CTU_EME	APPRO CORPORATE	DECAISSEMENT	INTERNAL	11	59	2025-01-21 15:50:46	2025-01-21 15:50:46	f	ACTIVE	14
128	ML_CTU_EME	APPRO CORPORATE	DECAISSEMENT	INTERNAL	11	60	2025-01-21 15:54:27	2025-01-21 15:54:27	f	ACTIVE	14
129	ML_MAT_EME	Transfert compte à sous compte	DECAISSEMENT	INTERNAL	6	60	2025-01-21 16:12:01	2025-01-21 16:12:01	f	ACTIVE	14
130	CI_MAT_EME	Transfert compte à sous compte	DECAISSEMENT	INTERNAL	6	59	2025-01-21 16:16:21	2025-01-21 16:16:21	f	ACTIVE	14
131	GN_CTU_EME	APPRO CORPORATE	DECAISSEMENT	INTERNAL	11	62	2025-01-21 16:29:05	2025-01-21 16:29:05	f	ACTIVE	14
132	GW_CTU_EME	APPRO CORPORATE	DECAISSEMENT	INTERNAL	11	81	2025-01-21 16:33:20	2025-01-21 16:33:20	f	ACTIVE	14
133	NE_CTU_EME	APPRO CORPORATE	DECAISSEMENT	INTERNAL	11	83	2025-01-21 16:37:52	2025-01-21 16:37:52	f	ACTIVE	14
134	BF_CTU_EME	APPRO CORPORATE	DECAISSEMENT	INTERNAL	11	63	2025-01-21 16:42:13	2025-01-21 16:42:13	f	ACTIVE	14
135	TG_CTU_EME	APPRO CORPORATE	DECAISSEMENT	INTERNAL	11	84	2025-01-21 16:50:00	2025-01-21 16:50:00	f	ACTIVE	14
136	BJ_CTU_EME	APPRO CORPORATE	DECAISSEMENT	INTERNAL	11	71	2025-01-21 16:55:08	2025-01-21 16:55:08	f	ACTIVE	14
137	NE_MAT_EME	Transfert compte à sous compte	DECAISSEMENT	INTERNAL	6	83	2025-01-21 17:05:31	2025-01-21 17:05:31	f	ACTIVE	14
138	BF_MAT_EME	Transfert compte à sous compte	DECAISSEMENT	INTERNAL	6	63	2025-01-21 17:06:22	2025-01-21 17:06:22	f	ACTIVE	14
139	GW_MAT_EME	Transfert compte à sous compte	DECAISSEMENT	INTERNAL	6	81	2025-01-21 17:07:31	2025-01-21 17:07:31	f	ACTIVE	14
140	TG_MAT_EME	Transfert compte à sous compte	DECAISSEMENT	INTERNAL	6	84	2025-01-21 17:08:33	2025-01-21 17:08:33	f	ACTIVE	14
141	BJ_MAT_EME	Transfert compte à sous compte	DECAISSEMENT	INTERNAL	6	71	2025-01-21 17:15:21	2025-01-21 17:15:21	f	ACTIVE	14
142	CI_CCP_EME	COMPENSE CORPORATE	ENCAISSEMENT	INTERNAL	12	59	2025-01-21 17:16:38	2025-01-21 17:16:38	f	ACTIVE	14
143	GW_CCP_EME	COMPENSE CORPORATE	ENCAISSEMENT	INTERNAL	12	81	2025-01-21 17:21:39	2025-01-21 17:21:39	f	ACTIVE	14
144	NE_CCP_EME	COMPENSE CORPORATE	ENCAISSEMENT	INTERNAL	12	83	2025-01-21 17:23:12	2025-01-21 17:23:12	f	ACTIVE	14
145	BF_CCP_EME	COMPENSE CORPORATE	ENCAISSEMENT	INTERNAL	12	63	2025-01-21 17:24:01	2025-01-21 17:24:01	f	ACTIVE	14
146	GN_CCP_EME	COMPENSE CORPORATE	ENCAISSEMENT	INTERNAL	12	62	2025-01-21 17:27:36	2025-01-21 17:27:36	f	ACTIVE	14
147	ML_CCP_EME	COMPENSE CORPORATE	ENCAISSEMENT	INTERNAL	12	60	2025-01-21 17:29:15	2025-01-21 17:29:15	f	ACTIVE	14
148	TG_CCP_EME	COMPENSE CORPORATE	ENCAISSEMENT	INTERNAL	12	84	2025-01-21 17:30:22	2025-01-21 17:30:22	f	ACTIVE	14
149	BJ_CCP_EME	COMPENSE CORPORATE	ENCAISSEMENT	INTERNAL	12	71	2025-01-21 17:32:27	2025-01-21 17:32:27	f	ACTIVE	14
150	GN_MAT_EME	Transfert compte à sous compte	DECAISSEMENT	INTERNAL	6	62	2025-01-22 12:47:03	2025-01-22 12:47:03	f	ACTIVE	14
151	ML_DPS_TPT	Transfert Touchpoint bulk ML	ENCAISSEMENT	EXTERNAL	1	60	2025-01-22 15:58:54	2025-01-22 15:58:54	f	ACTIVE	14
152	SN_BPM_WYF	FACTURIER WOYOFAL PARTENAIRE	ENCAISSEMENT	EXTERNAL	9	57	2025-01-23 12:28:46	2025-01-23 12:28:46	f	ACTIVE	47
153	SN_BPM_SNL	FACTURIER SENELEC PARTENAIRE	ENCAISSEMENT	EXTERNAL	9	57	2025-01-23 12:30:39	2025-01-23 12:30:39	f	ACTIVE	44
154	SN_BPM_SNU	FACTURIER SENEAU PARTENAIRE	ENCAISSEMENT	EXTERNAL	9	57	2025-01-23 12:31:34	2025-01-23 12:31:34	f	ACTIVE	43
155	SN_BPM_DPW	FACTURIER DPWORLD	ENCAISSEMENT	EXTERNAL	9	57	2025-01-23 12:32:31	2025-01-23 12:32:31	f	ACTIVE	45
156	SN_BPM_GMD	FACTURIER GRIMALDI	ENCAISSEMENT	EXTERNAL	9	57	2025-01-23 12:33:48	2025-01-23 12:33:48	f	ACTIVE	13
157	SN_BPM_BLR	FACTURIER BOLLORE	ENCAISSEMENT	EXTERNAL	9	57	2025-01-23 12:37:36	2025-01-23 12:37:36	f	ACTIVE	49
158	ML_MPM_WVE	PM WAVE ML	DECAISSEMENT	EXTERNAL	8	60	2025-01-23 13:53:43	2025-01-23 13:53:43	f	ACTIVE	8
159	ML_MPM_ORM	PM OM TOUCHPAY ML	DECAISSEMENT	EXTERNAL	8	60	2025-01-23 13:54:49	2025-01-23 13:54:49	f	ACTIVE	1
160	CI_DPS_MTN_API	DEPOT MTN LONACI CI	ENCAISSEMENT	EXTERNAL	1	59	2025-01-27 13:24:54	2025-01-27 13:24:54	f	ACTIVE	9
161	ML_DPS_TPT_CB	Transfert Touchpoint CB ML	ENCAISSEMENT	EXTERNAL	1	60	2025-01-27 17:17:03	2025-01-27 17:17:03	f	ACTIVE	14
162	ML_WDW_TPT_CB	Retrait Touchpoint ML CB	DECAISSEMENT	EXTERNAL	2	60	2025-01-27 17:18:04	2025-01-27 17:18:04	f	ACTIVE	14
163	ML_WDW_TPT_CC	Retrait Touchpoint cc ML	DECAISSEMENT	EXTERNAL	2	60	2025-01-27 17:20:43	2025-01-27 17:20:43	f	ACTIVE	14
164	ML_WDW_TPT	Retrait Touchpoint bulk ML	DECAISSEMENT	EXTERNAL	2	60	2025-01-27 17:23:13	2025-01-27 17:23:13	f	ACTIVE	14
165	ML_DPS_TPT_CC	Envoi Touchpoint cc ML	ENCAISSEMENT	EXTERNAL	1	60	2025-01-27 17:24:31	2025-01-27 17:24:31	f	ACTIVE	14
166	SN_DPS_WTU	ENVOI WESTERN UNION	ENCAISSEMENT	EXTERNAL	1	57	2025-01-30 10:00:27	2025-01-30 10:00:27	f	ACTIVE	54
167	SN_WDW_RIA	CASHOUT RIA	DECAISSEMENT	EXTERNAL	2	57	2025-01-30 10:02:09	2025-01-30 10:02:09	f	ACTIVE	55
168	SN_WDW_WTU	PAIEMENT WESTERN UNION	DECAISSEMENT	EXTERNAL	2	57	2025-01-30 10:06:56	2025-01-30 10:06:56	f	ACTIVE	54
169	SN_MPM_ORB	Carte Bancaire	DECAISSEMENT	EXTERNAL	8	57	2025-01-30 10:13:44	2025-01-30 10:13:44	f	ACTIVE	30
170	SN_DPS_RIA	Ria	ENCAISSEMENT	EXTERNAL	1	57	2025-01-30 10:17:56	2025-01-30 10:17:56	f	ACTIVE	55
171	SN_BPM_UCD	INSCRIPTION UCAD	ENCAISSEMENT	EXTERNAL	9	57	2025-01-30 10:19:40	2025-01-30 10:19:40	f	ACTIVE	51
172	SN_BPM_CPS	INSCRIPTION CAMPUSSEN	ENCAISSEMENT	EXTERNAL	9	57	2025-01-30 10:52:39	2025-01-30 10:52:39	f	ACTIVE	50
173	GN_WDW_TPT_CB	Retrait Touchpoint GN CB	DECAISSEMENT	EXTERNAL	2	62	2025-01-30 11:45:07	2025-01-30 11:45:07	f	ACTIVE	14
174	GN_DPS_TPT_CC	Envoi Touchpoint cc GN	ENCAISSEMENT	EXTERNAL	1	62	2025-01-30 11:46:06	2025-01-30 11:46:06	f	ACTIVE	14
175	GN_DPS_TPT_CB	Transfert Touchpoint CB GN	ENCAISSEMENT	EXTERNAL	1	62	2025-01-30 11:47:06	2025-01-30 11:47:06	f	ACTIVE	14
176	GN_WDW_TPT	Retrait Touchpoint bulk GN	DECAISSEMENT	EXTERNAL	2	62	2025-01-30 11:48:02	2025-01-30 11:48:02	f	ACTIVE	14
177	GN_WDW_TPT_CC	Retrait Touchpoint cc GN	DECAISSEMENT	EXTERNAL	2	62	2025-01-30 12:08:14	2025-01-30 12:08:14	f	ACTIVE	14
178	BF_WDW_MOV	CASHOUT MOOV BF	DECAISSEMENT	EXTERNAL	2	63	2025-01-30 12:21:35	2025-01-30 12:21:35	f	ACTIVE	10
179	BF_WDW_ORM	CASHOUT OM BF	DECAISSEMENT	EXTERNAL	2	63	2025-01-30 12:22:29	2025-01-30 12:22:29	f	ACTIVE	1
180	GN_WDW_ORM	Retrait Orange Money	DECAISSEMENT	EXTERNAL	2	62	2025-01-30 17:58:57	2025-02-03 18:01:04	f	ACTIVE	1
181	SN_WDW_WZL	CASHOUT WIZALL	DECAISSEMENT	EXTERNAL	2	57	2025-01-31 09:36:21	2025-01-31 09:36:21	f	ACTIVE	7
182	GN_MPM_ORM_OTP	ORANGE MONEY	DECAISSEMENT	EXTERNAL	8	62	2025-01-31 09:49:06	2025-01-31 09:49:06	f	ACTIVE	1
183	GN_MPM_EME	Paiement Touchpoint	DECAISSEMENT	INTERNAL	8	62	2025-01-31 09:59:48	2025-01-31 09:59:48	f	ACTIVE	14
184	GN_CCT_EME	Transfert Touchpoint	ENCAISSEMENT	INTERNAL	3	62	2025-01-31 10:00:49	2025-01-31 10:00:49	f	ACTIVE	14
185	ML_DPS_ECB	CASHIN ECOBANK ML	ENCAISSEMENT	EXTERNAL	1	60	2025-01-31 16:20:49	2025-01-31 16:20:49	f	ACTIVE	19
186	BF_ATM_MOV	Moov	ENCAISSEMENT	EXTERNAL	7	63	2025-02-03 09:48:00	2025-02-03 09:48:00	f	ACTIVE	10
187	GN_WDW_PYC	CASHOUT PAYCARD GN	DECAISSEMENT	EXTERNAL	2	62	2025-02-03 10:16:06	2025-02-03 10:16:06	f	ACTIVE	56
188	GN_DPS_PYC	DEPOT PAYCARD GN	ENCAISSEMENT	EXTERNAL	1	62	2025-02-03 10:16:51	2025-02-03 10:16:51	f	ACTIVE	56
189	ML_ATM_MOV	Moov	ENCAISSEMENT	EXTERNAL	7	60	2025-02-03 10:20:57	2025-02-03 10:20:57	f	ACTIVE	10
190	BF_MPM_ORM_OTP	ORANGE MONEY	DECAISSEMENT	EXTERNAL	8	63	2025-02-03 11:01:15	2025-02-03 11:01:15	f	ACTIVE	1
191	BF_CCT_EME	Transfert Touchpoint	ENCAISSEMENT	INTERNAL	3	63	2025-02-03 17:08:48	2025-02-03 17:08:48	f	ACTIVE	14
192	BF_MPM_EME	Paiement Touchpoint	DECAISSEMENT	INTERNAL	8	63	2025-02-03 17:14:58	2025-02-03 17:14:58	f	ACTIVE	14
193	BF_DPS_COR	DEPOT CORIS MONEY BF	ENCAISSEMENT	EXTERNAL	1	63	2025-02-04 12:31:14	2025-02-04 12:31:14	f	ACTIVE	57
194	BF_DPS_YND	ACHAT YENDA DATA BF	ENCAISSEMENT	EXTERNAL	1	63	2025-02-04 15:45:45	2025-02-04 15:45:45	f	ACTIVE	38
195	SN_ATM_HYO	Hayo	ENCAISSEMENT	EXTERNAL	7	57	2025-02-12 17:32:39	2025-02-12 17:32:39	f	ACTIVE	6
196	BF_DPS_TPT_CB	Transfert Touchpoint CB BF	ENCAISSEMENT	EXTERNAL	1	63	2025-02-13 09:46:44	2025-02-13 09:46:44	f	ACTIVE	14
197	BF_DPS_EME	BF Depot Wallet EME TP BF	ENCAISSEMENT	INTERNAL	1	63	2025-02-13 10:14:23	2025-02-13 10:14:23	f	ACTIVE	14
198	BF_WDW_TPT_CC	Retrait Touchpoint cc BF	DECAISSEMENT	EXTERNAL	2	63	2025-02-13 12:43:43	2025-02-13 12:43:43	f	ACTIVE	14
199	BF_WDW_TPT_CB	Retrait Touchpoint CB BF	DECAISSEMENT	EXTERNAL	2	63	2025-02-13 12:44:35	2025-02-13 12:44:35	f	ACTIVE	14
200	BF_WDW_TPT	Retrait Touchpoint bulk BF	DECAISSEMENT	EXTERNAL	2	63	2025-02-13 12:45:28	2025-02-13 12:45:28	f	ACTIVE	14
201	BF_DPS_TPT	Transfert Touchpoint bulk BF	ENCAISSEMENT	EXTERNAL	1	63	2025-02-13 12:46:22	2025-02-13 12:46:22	f	ACTIVE	14
202	BF_DPS_TPT_CC	Envoi Touchpoint cc BF	ENCAISSEMENT	EXTERNAL	1	63	2025-02-13 12:47:35	2025-02-13 12:47:35	f	ACTIVE	14
203	SN_BPM_DTN_ESIM	E-SIM DTONE	ENCAISSEMENT	EXTERNAL	9	57	2025-02-14 11:42:57	2025-02-14 11:42:57	f	ACTIVE	58
204	SN_BPM_ARL_ESIM	E-SIM AIRALO	ENCAISSEMENT	EXTERNAL	9	57	2025-02-14 11:44:09	2025-02-14 11:44:09	f	ACTIVE	59
205	CI_WDW_ORM	CASHOUT OM CI	DECAISSEMENT	EXTERNAL	2	59	2025-02-14 12:44:09	2025-02-14 12:44:09	f	ACTIVE	1
206	GN_DPS_EME	GN Depot Wallet EME TP	ENCAISSEMENT	INTERNAL	1	62	2025-02-14 12:46:57	2025-02-14 12:46:57	f	ACTIVE	14
207	CI_DPS_ECB	DEPOT ECOBANK CI	ENCAISSEMENT	EXTERNAL	1	59	2025-02-17 16:03:49	2025-02-17 16:03:49	f	ACTIVE	19
208	CI_WDW_ECB	CASHOUT ECOBANK CI	DECAISSEMENT	EXTERNAL	2	59	2025-02-17 16:06:32	2025-02-17 16:06:32	f	ACTIVE	19
209	CI_DPS_TRM	DEPOT TRESORMONEY CI	ENCAISSEMENT	EXTERNAL	1	59	2025-02-17 16:16:39	2025-02-17 16:16:39	f	ACTIVE	31
210	CI_WDW_TRM	CASHOUT TRESORMONEY CI	DECAISSEMENT	EXTERNAL	2	59	2025-02-17 16:22:44	2025-02-17 16:22:44	f	ACTIVE	31
211	SN_MPM_TPT	TouchPoint	DECAISSEMENT	EXTERNAL	8	57	2025-02-17 17:18:51	2025-02-17 17:18:51	f	ACTIVE	14
212	CI_DPS_ADV	DEPOT ADVANS CI	ENCAISSEMENT	EXTERNAL	1	59	2025-02-18 11:39:28	2025-02-18 11:39:28	f	ACTIVE	29
213	CI_WDW_ADV	CASHOUT ADVANS CI	DECAISSEMENT	EXTERNAL	2	59	2025-02-18 11:41:18	2025-02-18 11:41:18	f	ACTIVE	29
214	ML_BPM_ENG	FACTURE ENERGIA ML	ENCAISSEMENT	EXTERNAL	9	60	2025-02-18 12:15:31	2025-02-18 12:15:31	f	ACTIVE	60
215	CI_DPS_MAN	DEPOT MANSABANK CI	ENCAISSEMENT	EXTERNAL	1	59	2025-02-20 11:20:17	2025-02-20 11:20:17	f	ACTIVE	61
216	GN_UVT_EME	Transformation d'UV Agence Orange Money GN	DECAISSEMENT	INTERNAL	22	62	2025-02-20 17:57:18	2025-02-20 17:57:18	f	ACTIVE	1
217	GN_EMT_EME	Transformation d'UV Orange Money	ENCAISSEMENT	INTERNAL	21	62	2025-02-20 17:58:50	2025-02-20 17:58:50	f	ACTIVE	1
218	CI_BPM_CIE	FACTURE CIE CI	ENCAISSEMENT	EXTERNAL	9	59	2025-02-21 16:43:35	2025-02-21 16:43:35	f	ACTIVE	32
219	CI_BPM_SOD	FACTURE SODECI CI	ENCAISSEMENT	EXTERNAL	9	59	2025-02-21 16:45:19	2025-02-21 16:45:19	f	ACTIVE	33
220	ML_WDW_ECB	CASHOUT ECOBANK ML	DECAISSEMENT	EXTERNAL	2	60	2025-02-21 16:47:20	2025-02-21 16:47:20	f	ACTIVE	19
221	CI_DPS_PMB	DEPOT PREMIER BET CI	ENCAISSEMENT	EXTERNAL	1	59	2025-02-24 12:41:34	2025-02-24 12:41:34	f	ACTIVE	5
222	CI_DPS_LDW	DEPOT LEADWAY CI	ENCAISSEMENT	EXTERNAL	1	59	2025-02-25 15:48:24	2025-02-25 15:48:24	f	ACTIVE	34
223	SN_BPM_RPD	FACTURIER RAPIDO PARTENAIRE	ENCAISSEMENT	EXTERNAL	9	57	2025-02-27 16:38:32	2025-02-27 16:38:32	f	ACTIVE	48
224	SN_DPS_TPT_DIGICASH	Pay digicash TP	ENCAISSEMENT	EXTERNAL	1	57	2025-02-28 10:31:23	2025-02-28 10:31:23	f	ACTIVE	14
225	SN_BPM_CGL	FACTURIER COGELEC	ENCAISSEMENT	EXTERNAL	9	57	2025-03-07 16:38:46	2025-03-07 16:38:46	f	ACTIVE	46
226	SN_BPM_DTN	CASHIN DTONE	ENCAISSEMENT	EXTERNAL	9	57	2025-03-13 08:56:23	2025-03-13 08:56:23	f	ACTIVE	58
227	SN_WDW_WZL_BON	CASHOUT BON WIZALL	DECAISSEMENT	EXTERNAL	2	57	2025-03-14 10:52:48	2025-03-14 10:52:48	f	ACTIVE	7
228	SN_DPS_COR	Coris Money 	ENCAISSEMENT	EXTERNAL	1	57	2025-03-18 10:46:59	2025-03-18 10:46:59	f	ACTIVE	57
229	SN_WDW_COR	CASHOUT CORIS MONEY	DECAISSEMENT	EXTERNAL	2	57	2025-03-18 10:48:01	2025-03-18 10:48:01	f	ACTIVE	57
230	ML_DPS_SAM	CASHIN SAMAMONEY ML	ENCAISSEMENT	EXTERNAL	1	60	2025-03-18 12:34:57	2025-03-18 12:34:57	f	ACTIVE	20
231	CI_WDW_MAN	CASHOUT MANSABANK CI	DECAISSEMENT	EXTERNAL	2	59	2025-03-19 11:22:58	2025-03-19 11:22:58	f	ACTIVE	61
232	SN_AMT_EME	Transfert sous compte à  compte	ENCAISSEMENT	INTERNAL	5	57	2025-04-11 16:47:03	2025-04-11 16:47:03	f	ACTIVE	14
233	SN_STU_EME	Appro Fournisseur Service	ENCAISSEMENT	INTERNAL	18	57	2025-04-14 15:18:50	2025-04-14 15:18:50	f	ACTIVE	14
234	SN_SCP_EME	Compense Fournisseur Service	DECAISSEMENT	INTERNAL	19	57	2025-04-14 15:20:30	2025-04-14 15:20:30	f	ACTIVE	14
235	BF_WDW_COR	CASHOUT CORIS MONEY BF	DECAISSEMENT	EXTERNAL	2	63	2025-04-18 17:43:44	2025-04-18 17:43:44	f	ACTIVE	57
236	BJ_AMT_EME	Transfert sous compte à  compte	ENCAISSEMENT	INTERNAL	5	71	2025-05-06 14:24:37	2025-05-06 14:24:37	f	ACTIVE	14
237	BJ_WDW_MTN	DEPOT MTN BJ	ENCAISSEMENT	EXTERNAL	2	71	2025-05-06 15:52:30	2025-05-06 15:52:30	f	ACTIVE	9
238	TG_AMT_EME	Transfert sous compte à  compte	ENCAISSEMENT	INTERNAL	5	84	2025-05-06 17:00:50	2025-05-06 17:00:50	f	ACTIVE	14
239	SN_CCT_TPT	 Transfert PI 	ENCAISSEMENT	PI	3	57	2025-07-24 12:37:18	2025-07-24 12:37:18	f	ACTIVE	14
240	SN_MPM_TPT_REC	Demande de paiement reception	ENCAISSEMENT	PI	8	57	2025-07-24 12:39:24	2025-07-24 12:39:24	f	ACTIVE	14
241	SN_CCT_TPT_INTRA	Intra Transfert PI	ENCAISSEMENT	PI	3	57	2025-07-24 12:40:02	2025-07-24 12:40:02	f	ACTIVE	14
242	SN_CCT_TPT_PI	Transfert PI From External	DECAISSEMENT	PI	3	57	2025-08-06 10:09:00	2025-08-06 10:09:00	f	ACTIVE	14
243	SN_MPM_TPT_SEND	Demande de PAIEMENT	DECAISSEMENT	PI	8	57	2025-08-06 17:19:59	2025-08-06 17:19:59	f	ACTIVE	14
244	CI_AMT_EME	Transfert sous compte à compte	DECAISSEMENT	INTERNAL	5	59	2025-08-21 18:50:19	2025-08-21 18:50:19	f	ACTIVE	14
245	BF_AMT_EME	Transfert sous compte à compte	DECAISSEMENT	INTERNAL	5	63	2025-08-22 12:33:40	2025-08-22 12:33:40	f	ACTIVE	14
246	ML_AMT_EME	Transfert sous compte à compte	DECAISSEMENT	INTERNAL	5	60	2025-08-22 13:02:40	2025-08-22 13:02:40	f	ACTIVE	14
247	SN_WDW_EME	Retrait Wallet EME TP	DECAISSEMENT	INTERNAL	2	57	2025-08-29 09:43:14	2025-08-29 09:43:14	f	ACTIVE	14
248	CI_CCT_TPT	 Transfert PI 	ENCAISSEMENT	PI	3	59	2025-11-26 12:02:16	2025-11-26 12:02:16	f	ACTIVE	14
249	CI_CCT_TPT_INTRA	Intra Transfert PI	ENCAISSEMENT	PI	3	59	2025-11-26 12:05:11	2025-11-26 12:05:11	f	ACTIVE	14
250	CI_CCT_TPT_PI	Transfert PI From External	DECAISSEMENT	PI	3	59	2025-11-26 12:07:21	2025-11-26 12:07:21	f	ACTIVE	14
251	CI_MPM_TPT_SEND	Demande de PAIEMENT	DECAISSEMENT	PI	8	59	2025-11-26 12:08:51	2025-11-27 10:12:32	f	ACTIVE	14
252	CI_MPM_TPT_REC	Demande de paiement reception	ENCAISSEMENT	PI	8	59	2025-11-26 12:11:16	2025-11-26 12:11:16	f	ACTIVE	14
253	SN_DPS_EME_DIGICASH	Pay digicash TP	ENCAISSEMENT	INTERNAL	1	57	2025-12-09 15:51:14	2025-12-09 15:51:14	f	ACTIVE	14
\.


--
-- Data for Name: service_provider; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.service_provider (id, provider_id, flow_id, ranking, url, gateway, creation_date, updated_date, deleted, status) FROM stdin;
\.


--
-- Data for Name: service_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.service_type (id, code, short_code, label, movement_type, creation_date, updated_date, deleted, status) FROM stdin;
26	TDS_TOPUP	TTU	Approvisionnement TDS	OPERATION	2025-01-21 10:44:42	2025-01-21 10:44:42	f	ACTIVE
1	DEPOSIT	DPS	Depot	TRANSACTION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
2	WITHDRAWAL	WDW	Retrait	TRANSACTION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
3	C2C_TRANSFER	CCT	Transfert d'UV Client vers Client	TRANSACTION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
4	A2A_TRANSFER	AAT	Transfert d'UV Agent vers Agent	OPERATION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
5	A2M_TRANSFER	AMT	Transfert d'UV Agent vers Master	OPERATION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
6	M2A_TRANSFER	MAT	Transfert d'UV Master vers Agent	OPERATION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
7	AIRTIME	ATM	Achat de Crédit	TRANSACTION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
8	MERCHANT_PAYMENT	MPM	Paiement Marchand	TRANSACTION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
9	BILLS_PAYMENT	BPM	Paiement Facture	TRANSACTION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
10	SALARY_PAYMENT	SPM	Paiement salaire	TRANSACTION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
11	CLIENT_TOPUP	CTU	Approvisionnement Client	OPERATION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
12	CLIENT_COMPENSATION	CCP	Compense Client	OPERATION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
13	CLIENT_REPAYMENT	CRP	Remboursement d'UV (Master Agent et Agent)	OPERATION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
14	CUSTOMER_REFUND	CRF	Remboursement sur wallet suite à une transaction annulée	TRANSACTION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
15	E_MONEY_DESCTRUCTION	EMD	Destruction de Monnaie electronique	OPERATION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
16	REGISTRATION	RGT	Enrollement online ou par agent	OPERATION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
17	KYC1_2_KYC2	KK3	Passage KYC1 vers KYC2	OPERATION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
18	SUPPLIER_TOPUP	STU	Approvisionnement Fournisseur	OPERATION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
19	SUPPLIER_COMPENSATION	SCP	Compense Fournisseur	OPERATION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
20	PROVIDER_REPAYMENT	PRP	Remboursement d'UV	OPERATION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
21	E_MONEY_TRANSFORMATION	EMT	Transformation de Monnaie Electronique en UV Fournisseur	OPERATION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
22	FLOAT_TRANSFORMATION	UVT	Transformation UV Fournisseur en Monnaie Electronique	OPERATION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
23	E_MONEY_CREATION	EMC	Création de Monnaie electronique	OPERATION	2024-12-02 13:19:32	2024-12-02 13:19:32	f	ACTIVE
24	BALANCE_MIGRATION	BLM	Migration de solde Agence	OPERATION	2024-12-17 15:11:15	2024-12-17 15:11:15	f	ACTIVE
25	BANK_TOPUP	BTU	Approvisionnement compte bank	OPERATION	2024-12-20 13:01:13	2024-12-20 13:01:13	f	ACTIVE
\.


--
-- Data for Name: status; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.status (id, code, label, message, creation_date, updated_date, deleted, status) FROM stdin;
1	BK_INITIATED	BK_INITIATED	BK_INITIATED	2024-05-09 00:00:00	2024-05-09 00:00:00	f	ACTIVE
2	BK_FAILED	BK_FAILED	BK_FAILED	2024-05-09 00:00:00	2024-05-09 00:00:00	f	ACTIVE
3	BK_LOADED	BK_LOADED	BK_LOADED	2024-05-09 00:00:00	2024-05-09 00:00:00	f	ACTIVE
4	PART_INITIATED	PART_INITIATED	PART_INITIATED	2024-05-09 00:00:00	2024-05-09 00:00:00	f	ACTIVE
5	PART_LOADED	PART_LOADED	PART_LOADED	2024-05-09 00:00:00	2024-05-09 00:00:00	f	ACTIVE
6	PART_SUCCESSFUL	PART_SUCCESSFUL	PART_SUCCESSFUL	2024-05-09 00:00:00	2024-05-09 00:00:00	f	ACTIVE
7	PART_FAILED	PART_FAILED	PART_FAILED	2024-05-09 00:00:00	2024-05-09 00:00:00	f	ACTIVE
8	SUCCESSFUL	SUCCESSFUL	SUCCESSFUL	2024-05-09 00:00:00	2024-05-09 00:00:00	f	ACTIVE
9	CANCELLATION_REQUEST	CANCELLATION_REQUEST	CANCELLATION_REQUEST	2024-05-09 00:00:00	2024-05-09 00:00:00	f	ACTIVE
10	CANCELLED	CANCELLED	CANCELLED	2024-05-09 00:00:00	2024-05-09 00:00:00	f	ACTIVE
11	BK_SUCCESSFUL	BK_SUCCESSFUL	BK_SUCCESSFUL	2024-05-09 00:00:00	2024-05-09 00:00:00	f	ACTIVE
12	ACCOUNTED	ACCOUNTED	ACCOUNTED	2025-03-04 15:23:12	2025-03-04 15:23:37	f	ACTIVE
13	SUCCESS_RECONCILED	SUCCESS_RECONCILED	SUCCESS_RECONCILED	2025-04-10 12:18:50	2025-04-10 12:19:06	f	ACTIVE
14	RECONCILED_KO	RECONCILED_KO	RECONCILED_KO	2025-04-10 12:18:52	2025-04-10 12:19:07	f	ACTIVE
\.


--
-- Data for Name: status_history; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.status_history (id, status, creation_date, message, author, gu_id) FROM stdin;
1	BK_LOADED	2025-12-28 20:28:51.755643	BK_LOADED	701111111	2658b1d4-6f4a-4a19-8996-b76dca95c497
2	BK_SUCCESSFUL	2025-12-28 20:28:51.84628	BK_SUCCESSFUL	701111111	2658b1d4-6f4a-4a19-8996-b76dca95c497
3	SUCCESSFUL	2025-12-28 20:28:51.87044	SUCCESSFUL	701111111	2658b1d4-6f4a-4a19-8996-b76dca95c497
4	BK_LOADED	2025-12-28 20:40:30.649008	BK_LOADED	701111111	946bc542-de2e-4cb7-b775-b305de917e30
5	BK_SUCCESSFUL	2025-12-28 20:40:30.761595	BK_SUCCESSFUL	701111111	946bc542-de2e-4cb7-b775-b305de917e30
6	BK_LOADED	2025-12-28 20:49:49.874583	BK_LOADED	701111111	1d792985-6d0d-48c6-9e10-265285139c55
7	BK_SUCCESSFUL	2025-12-28 20:49:49.988033	BK_SUCCESSFUL	701111111	1d792985-6d0d-48c6-9e10-265285139c55
8	BK_LOADED	2025-12-28 20:52:26.834206	BK_LOADED	701111111	4706a12d-d06c-4434-a032-3e170ef1eec4
9	BK_SUCCESSFUL	2025-12-28 20:52:26.975228	BK_SUCCESSFUL	701111111	4706a12d-d06c-4434-a032-3e170ef1eec4
10	SUCCESSFUL	2025-12-28 20:52:27.009882	SUCCESSFUL	701111111	4706a12d-d06c-4434-a032-3e170ef1eec4
11	BK_LOADED	2025-12-28 21:06:26.616804	BK_LOADED	701111111	021842cc-3a31-4500-9429-e974e4a2a4e0
12	BK_SUCCESSFUL	2025-12-28 21:06:26.924599	BK_SUCCESSFUL	701111111	021842cc-3a31-4500-9429-e974e4a2a4e0
13	BK_LOADED	2025-12-28 21:19:09.516389	BK_LOADED	701111111	4c52a327-c3fa-4870-9f4a-f7c3eee5c570
14	BK_SUCCESSFUL	2025-12-28 21:19:09.669242	BK_SUCCESSFUL	701111111	4c52a327-c3fa-4870-9f4a-f7c3eee5c570
15	BK_LOADED	2025-12-28 21:23:54.845033	BK_LOADED	701111111	99522051-e390-40a8-94a1-643dfdf30f1f
16	BK_SUCCESSFUL	2025-12-28 21:23:55.021263	BK_SUCCESSFUL	701111111	99522051-e390-40a8-94a1-643dfdf30f1f
17	BK_LOADED	2025-12-28 21:40:14.297563	BK_LOADED	701111111	1d85b2eb-dc9f-4748-9767-408f1658fde2
18	BK_SUCCESSFUL	2025-12-28 21:40:14.511856	BK_SUCCESSFUL	701111111	1d85b2eb-dc9f-4748-9767-408f1658fde2
19	SUCCESSFUL	2025-12-28 21:40:14.563554	SUCCESSFUL	701111111	1d85b2eb-dc9f-4748-9767-408f1658fde2
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, email, username, hashed_password, is_active, is_superuser, creation_date, updated_date, deleted, status) FROM stdin;
1	admin@admin.com	admin	$2b$12$GDk/5Cl6m9Ifai5zVblQqen95lRICNKt8JSz6G6zkq40794crUCNu	t	f	2025-12-27 10:16:44.930322	2025-12-27 10:16:44.930322	f	ACTIVE
\.


--
-- Name: account_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.account_id_seq', 13, true);


--
-- Name: account_role_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.account_role_id_seq', 1, false);


--
-- Name: account_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.account_type_id_seq', 1, false);


--
-- Name: balance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.balance_id_seq', 4, true);


--
-- Name: bank_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.bank_id_seq', 1, false);


--
-- Name: client_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.client_id_seq', 1, false);


--
-- Name: flow_constraint_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.flow_constraint_id_seq', 1, false);


--
-- Name: flow_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.flow_id_seq', 2, true);


--
-- Name: impact_rule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.impact_rule_id_seq', 8, true);


--
-- Name: impact_rule_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.impact_rule_type_id_seq', 1, false);


--
-- Name: interval_rule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.interval_rule_id_seq', 4, true);


--
-- Name: legal_entity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.legal_entity_id_seq', 1, false);


--
-- Name: movement_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.movement_id_seq', 19, true);


--
-- Name: operation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.operation_id_seq', 4, true);


--
-- Name: operator_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.operator_id_seq', 1, false);


--
-- Name: product_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.product_id_seq', 1, false);


--
-- Name: provider_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.provider_id_seq', 1, false);


--
-- Name: rule_account_role_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.rule_account_role_id_seq', 8, true);


--
-- Name: service_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.service_id_seq', 1, false);


--
-- Name: service_provider_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.service_provider_id_seq', 1, false);


--
-- Name: service_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.service_type_id_seq', 1, false);


--
-- Name: status_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.status_history_id_seq', 19, true);


--
-- Name: status_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.status_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: operation UniqueAmountAccountNumberGuIDImpactRuleCode; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.operation
    ADD CONSTRAINT "UniqueAmountAccountNumberGuIDImpactRuleCode" UNIQUE (amount, account_number, gu_id, impact_rule_code);


--
-- Name: account account_account_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account
    ADD CONSTRAINT account_account_number_key UNIQUE (account_number);


--
-- Name: account_account_type account_account_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account_account_type
    ADD CONSTRAINT account_account_type_pkey PRIMARY KEY (id_account, id_account_type);


--
-- Name: account account_merchant_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account
    ADD CONSTRAINT account_merchant_code_key UNIQUE (merchant_code);


--
-- Name: account account_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account
    ADD CONSTRAINT account_pkey PRIMARY KEY (id);


--
-- Name: account_role account_role_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account_role
    ADD CONSTRAINT account_role_pkey PRIMARY KEY (id);


--
-- Name: account_type account_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account_type
    ADD CONSTRAINT account_type_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: balance balance_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.balance
    ADD CONSTRAINT balance_pkey PRIMARY KEY (id);


--
-- Name: bank bank_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bank
    ADD CONSTRAINT bank_pkey PRIMARY KEY (id);


--
-- Name: client client_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client
    ADD CONSTRAINT client_pkey PRIMARY KEY (id);


--
-- Name: country country_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.country
    ADD CONSTRAINT country_pkey PRIMARY KEY (iso_code);


--
-- Name: flow_constraint flow_constraint_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.flow_constraint
    ADD CONSTRAINT flow_constraint_pkey PRIMARY KEY (id);


--
-- Name: flow flow_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.flow
    ADD CONSTRAINT flow_pkey PRIMARY KEY (id);


--
-- Name: impact_rule impact_rule_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.impact_rule
    ADD CONSTRAINT impact_rule_pkey PRIMARY KEY (id);


--
-- Name: impact_rule_type impact_rule_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.impact_rule_type
    ADD CONSTRAINT impact_rule_type_pkey PRIMARY KEY (id);


--
-- Name: interval_rule interval_rule_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.interval_rule
    ADD CONSTRAINT interval_rule_pkey PRIMARY KEY (id);


--
-- Name: legal_entity legal_entity_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.legal_entity
    ADD CONSTRAINT legal_entity_pkey PRIMARY KEY (id);


--
-- Name: movement movement_gu_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movement
    ADD CONSTRAINT movement_gu_id_key UNIQUE (gu_id);


--
-- Name: movement movement_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movement
    ADD CONSTRAINT movement_pkey PRIMARY KEY (id);


--
-- Name: operation operation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.operation
    ADD CONSTRAINT operation_pkey PRIMARY KEY (id);


--
-- Name: operator operator_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.operator
    ADD CONSTRAINT operator_pkey PRIMARY KEY (id);


--
-- Name: product product_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT product_pkey PRIMARY KEY (id);


--
-- Name: provider provider_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.provider
    ADD CONSTRAINT provider_pkey PRIMARY KEY (id);


--
-- Name: rule_account_role rule_account_role_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rule_account_role
    ADD CONSTRAINT rule_account_role_pkey PRIMARY KEY (id);


--
-- Name: service service_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service
    ADD CONSTRAINT service_pkey PRIMARY KEY (id);


--
-- Name: service_provider service_provider_flow_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service_provider
    ADD CONSTRAINT service_provider_flow_id_key UNIQUE (flow_id);


--
-- Name: service_provider service_provider_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service_provider
    ADD CONSTRAINT service_provider_pkey PRIMARY KEY (id);


--
-- Name: service_type service_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service_type
    ADD CONSTRAINT service_type_pkey PRIMARY KEY (id);


--
-- Name: status status_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.status
    ADD CONSTRAINT status_code_key UNIQUE (code);


--
-- Name: status_history status_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.status_history
    ADD CONSTRAINT status_history_pkey PRIMARY KEY (id);


--
-- Name: status status_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.status
    ADD CONSTRAINT status_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_account_role_identifier; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_account_role_identifier ON public.account_role USING btree (identifier);


--
-- Name: idx_account_role_identifier_deleted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_account_role_identifier_deleted ON public.account_role USING btree (identifier, deleted);


--
-- Name: idx_account_type_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_account_type_code ON public.account_type USING btree (code);


--
-- Name: idx_account_type_code_deleted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_account_type_code_deleted ON public.account_type USING btree (code, deleted);


--
-- Name: idx_agent_login; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_agent_login ON public.movement USING btree (agent_login);


--
-- Name: idx_bank_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bank_code ON public.bank USING btree (code);


--
-- Name: idx_bank_code_deleted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bank_code_deleted ON public.bank USING btree (code, deleted);


--
-- Name: idx_client_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_client_id ON public.movement USING btree (client_id);


--
-- Name: idx_composite_accountNumber_opDate; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "idx_composite_accountNumber_opDate" ON public.operation USING btree (account_number, op_date);


--
-- Name: idx_flow_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_flow_code ON public.flow USING btree (code);


--
-- Name: idx_flow_code_deleted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_flow_code_deleted ON public.flow USING btree (code, deleted);


--
-- Name: idx_flow_constraint_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_flow_constraint_code ON public.flow_constraint USING btree (code);


--
-- Name: idx_flow_constraint_code_deleted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_flow_constraint_code_deleted ON public.flow_constraint USING btree (code, deleted);


--
-- Name: idx_flow_service_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_flow_service_code ON public.flow USING btree (service_code);


--
-- Name: idx_gu_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_gu_id ON public.movement USING btree (gu_id);


--
-- Name: idx_gu_id_op; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_gu_id_op ON public.operation USING btree (gu_id);


--
-- Name: idx_impact_rule_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_impact_rule_code ON public.impact_rule USING btree (code);


--
-- Name: idx_impact_rule_code_deleted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_impact_rule_code_deleted ON public.impact_rule USING btree (code, deleted);


--
-- Name: idx_impact_rule_type_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_impact_rule_type_code ON public.impact_rule_type USING btree (code);


--
-- Name: idx_impact_rule_type_code_deleted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_impact_rule_type_code_deleted ON public.impact_rule_type USING btree (code, deleted);


--
-- Name: idx_issuer_account; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_issuer_account ON public.movement USING btree (issuer_account);


--
-- Name: idx_legal_entity_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_legal_entity_code ON public.movement USING btree (legal_entity_code);


--
-- Name: idx_merchant_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_merchant_code ON public.movement USING btree (merchant_code);


--
-- Name: idx_partner_dist_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_partner_dist_id ON public.movement USING btree (partner_dist_id);


--
-- Name: idx_partner_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_partner_id ON public.movement USING btree (partner_id);


--
-- Name: idx_product_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_product_code ON public.movement USING btree (product_code);


--
-- Name: idx_product_codep; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_product_codep ON public.product USING btree (code);


--
-- Name: idx_reference_bulk; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_reference_bulk ON public.movement USING btree (reference_bulk);


--
-- Name: idx_service_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_service_code ON public.movement USING btree (service_code);


--
-- Name: idx_status_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_status_code ON public.movement USING btree (status_code);


--
-- Name: idx_status_codep; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_status_codep ON public.status USING btree (code);


--
-- Name: idx_status_history_gu_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_status_history_gu_id ON public.status_history USING btree (gu_id);


--
-- Name: idx_user_login; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_login ON public.movement USING btree (user_login);


--
-- Name: index_account_number; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX index_account_number ON public.operation USING btree (account_number);


--
-- Name: index_creation_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX index_creation_date ON public.movement USING btree (creation_date);


--
-- Name: index_impact_rule_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX index_impact_rule_code ON public.operation USING btree (impact_rule_code);


--
-- Name: index_op_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX index_op_date ON public.operation USING btree (op_date);


--
-- Name: movement movement_status_change; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER movement_status_change BEFORE UPDATE ON public.movement FOR EACH ROW WHEN (((old.status_code)::text IS DISTINCT FROM (new.status_code)::text)) EXECUTE FUNCTION public.movement_status_change_trigger();


--
-- Name: operation operation_before_insert; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER operation_before_insert BEFORE INSERT ON public.operation FOR EACH ROW EXECUTE FUNCTION public.operation_before_insert_trigger();


--
-- Name: account_account_type account_account_type_id_account_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account_account_type
    ADD CONSTRAINT account_account_type_id_account_fkey FOREIGN KEY (id_account) REFERENCES public.account(id);


--
-- Name: account_account_type account_account_type_id_account_type_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account_account_type
    ADD CONSTRAINT account_account_type_id_account_type_fkey FOREIGN KEY (id_account_type) REFERENCES public.account_type(id);


--
-- Name: account account_balance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account
    ADD CONSTRAINT account_balance_id_fkey FOREIGN KEY (balance_id) REFERENCES public.balance(id);


--
-- Name: account account_bank_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account
    ADD CONSTRAINT account_bank_id_fkey FOREIGN KEY (bank_id) REFERENCES public.bank(id);


--
-- Name: account account_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account
    ADD CONSTRAINT account_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.client(id);


--
-- Name: account account_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account
    ADD CONSTRAINT account_country_id_fkey FOREIGN KEY (country_id) REFERENCES public.country(iso_code);


--
-- Name: account account_legal_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account
    ADD CONSTRAINT account_legal_entity_id_fkey FOREIGN KEY (legal_entity_id) REFERENCES public.legal_entity(id);


--
-- Name: account account_parent_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account
    ADD CONSTRAINT account_parent_account_id_fkey FOREIGN KEY (parent_account_id) REFERENCES public.account(id);


--
-- Name: account account_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account
    ADD CONSTRAINT account_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.provider(id);


--
-- Name: flow_constraint flow_constraint_flow_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.flow_constraint
    ADD CONSTRAINT flow_constraint_flow_id_fkey FOREIGN KEY (flow_id) REFERENCES public.flow(id);


--
-- Name: flow_constraint flow_constraint_service_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.flow_constraint
    ADD CONSTRAINT flow_constraint_service_type_id_fkey FOREIGN KEY (service_type_id) REFERENCES public.service_type(id);


--
-- Name: impact_rule impact_rule_flow_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.impact_rule
    ADD CONSTRAINT impact_rule_flow_id_fkey FOREIGN KEY (flow_id) REFERENCES public.flow(id);


--
-- Name: impact_rule impact_rule_impact_rule_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.impact_rule
    ADD CONSTRAINT impact_rule_impact_rule_type_id_fkey FOREIGN KEY (impact_rule_type_id) REFERENCES public.impact_rule_type(id);


--
-- Name: impact_rule impact_rule_rule_account_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.impact_rule
    ADD CONSTRAINT impact_rule_rule_account_role_id_fkey FOREIGN KEY (rule_account_role_id) REFERENCES public.rule_account_role(id);


--
-- Name: interval_rule interval_rule_impact_rule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.interval_rule
    ADD CONSTRAINT interval_rule_impact_rule_id_fkey FOREIGN KEY (impact_rule_id) REFERENCES public.impact_rule(id);


--
-- Name: legal_entity legal_entity_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.legal_entity
    ADD CONSTRAINT legal_entity_country_id_fkey FOREIGN KEY (country_id) REFERENCES public.country(iso_code);


--
-- Name: service service_legal_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service
    ADD CONSTRAINT service_legal_entity_id_fkey FOREIGN KEY (legal_entity_id) REFERENCES public.legal_entity(id);


--
-- Name: service_provider service_provider_flow_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service_provider
    ADD CONSTRAINT service_provider_flow_id_fkey FOREIGN KEY (flow_id) REFERENCES public.flow(id);


--
-- Name: service_provider service_provider_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service_provider
    ADD CONSTRAINT service_provider_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.provider(id);


--
-- Name: service service_service_operator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service
    ADD CONSTRAINT service_service_operator_id_fkey FOREIGN KEY (service_operator_id) REFERENCES public.operator(id);


--
-- Name: service service_service_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service
    ADD CONSTRAINT service_service_type_id_fkey FOREIGN KEY (service_type_id) REFERENCES public.service_type(id);


--
-- PostgreSQL database dump complete
--

\unrestrict IninvoHJhhGj0crCGxketB7vIx5myLMCpHYtgGf0Kwjt7NOT6R3BQUabFAu0EnO

