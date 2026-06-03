-- ============================================================================
-- Unified Users View - Automatically Syncs with Source Tables
-- ============================================================================
-- This script creates a unified view that automatically reflects changes
-- from shellcast_nc.users, shellcast_sc.users, and shellcast_fl.users
--
-- IMPORTANT: Views are read-only queries that execute in real-time.
-- Changes to source tables are IMMEDIATELY visible when querying the view.
-- No sync mechanism needed!
--
-- Column set matches shellcast_create_db_{nc,sc,fl}.sql (email/phone verification
-- fields use email_verified*, phone_verified*, phone_verif_* — not legacy
-- email_verification_sent / text_verification_sent).
-- ============================================================================

-- Create unified database (if it doesn't exist)
CREATE DATABASE IF NOT EXISTS shellcast_unified;

USE shellcast_unified;

-- Drop view if it already exists (for re-running this script)
DROP VIEW IF EXISTS all_users;

-- ============================================================================
-- Create Unified View
-- ============================================================================

CREATE VIEW all_users AS
SELECT
    'NC' AS state,
    id,
    firebase_uid,
    phone_number,
    email,
    email_pref,
    text_pref,
    COALESCE(text_consent, 0) AS text_consent,
    prob_pref,
    email_opt_in_date,
    text_opt_in_date,
    email_opt_out_date,
    text_opt_out_date,
    COALESCE(email_verified, 0) AS email_verified,
    email_verified_at,
    COALESCE(phone_verified, 0) AS phone_verified,
    phone_verified_at,
    phone_verif_count,
    phone_verif_count_date,
    deleted,
    created,
    updated
FROM shellcast_nc.users
WHERE deleted = 0

UNION ALL

SELECT
    'SC' AS state,
    id,
    firebase_uid,
    phone_number,
    email,
    email_pref,
    text_pref,
    text_consent,
    prob_pref,
    email_opt_in_date,
    text_opt_in_date,
    email_opt_out_date,
    text_opt_out_date,
    email_verified,
    email_verified_at,
    phone_verified,
    phone_verified_at,
    phone_verif_count,
    phone_verif_count_date,
    deleted,
    created,
    updated
FROM shellcast_sc.users
WHERE deleted = 0

UNION ALL

SELECT
    'FL' AS state,
    id,
    firebase_uid,
    phone_number,
    email,
    email_pref,
    text_pref,
    text_consent,
    prob_pref,
    email_opt_in_date,
    text_opt_in_date,
    email_opt_out_date,
    text_opt_out_date,
    email_verified,
    email_verified_at,
    phone_verified,
    phone_verified_at,
    phone_verif_count,
    phone_verif_count_date,
    deleted,
    created,
    updated
FROM shellcast_fl.users
WHERE deleted = 0;

-- ============================================================================
-- Grant Permissions
-- ============================================================================
-- Example (uncomment and modify):
-- GRANT SELECT ON shellcast_unified.all_users TO 'your_db_user'@'%';
-- FLUSH PRIVILEGES;
