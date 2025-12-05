-- ============================================================================
-- Unified Users View - Automatically Syncs with Source Tables
-- ============================================================================
-- This script creates a unified view that automatically reflects changes
-- from shellcast_nc.users, shellcast_sc.users, and shellcast_fl.users
--
-- IMPORTANT: Views are read-only queries that execute in real-time.
-- Changes to source tables are IMMEDIATELY visible when querying the view.
-- No sync mechanism needed!
-- ============================================================================

-- Create unified database (if it doesn't exist)
CREATE DATABASE IF NOT EXISTS shellcast_unified;

USE shellcast_unified;

-- Drop view if it already exists (for re-running this script)
DROP VIEW IF EXISTS all_users;

-- ============================================================================
-- Create Unified View
-- ============================================================================
-- This view automatically queries all three state databases in real-time.
-- When you SELECT from this view, it queries the actual tables, so
-- changes are immediately reflected.
-- ============================================================================

CREATE VIEW all_users AS
SELECT
    'NC' AS state,
    id,
    firebase_uid,
    phone_number,
    email,
    email_pref,
    COALESCE(email_consent, 0) AS email_consent,  -- Handle NULL if column doesn't exist in NC
    text_pref,
    COALESCE(text_consent, 0) AS text_consent,     -- Handle NULL if column doesn't exist in NC
    prob_pref,
    email_opt_in_date,
    text_opt_in_date,
    email_opt_out_date,
    text_opt_out_date,
    COALESCE(email_verification_sent, 0) AS email_verification_sent,
    COALESCE(text_verification_sent, 0) AS text_verification_sent,
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
    email_consent,
    text_pref,
    text_consent,
    prob_pref,
    email_opt_in_date,
    text_opt_in_date,
    email_opt_out_date,
    text_opt_out_date,
    email_verification_sent,
    text_verification_sent,
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
    email_consent,
    text_pref,
    text_consent,
    prob_pref,
    email_opt_in_date,
    text_opt_in_date,
    email_opt_out_date,
    text_opt_out_date,
    email_verification_sent,
    text_verification_sent,
    deleted,
    created,
    updated
FROM shellcast_fl.users
WHERE deleted = 0;

-- ============================================================================
-- Grant Permissions
-- ============================================================================
-- Grant SELECT permission to your database users
-- Replace 'your_db_user' with your actual database username(s)
-- You may need separate grants for each state's database user

-- Example (uncomment and modify):
-- GRANT SELECT ON shellcast_unified.all_users TO 'your_db_user'@'%';
-- FLUSH PRIVILEGES;

-- ============================================================================
-- Usage Examples
-- ============================================================================

-- Query all users across all states:
-- SELECT * FROM shellcast_unified.all_users;

-- Query users by state:
-- SELECT * FROM shellcast_unified.all_users WHERE state = 'NC';

-- Count users by state:
-- SELECT state, COUNT(*) as user_count FROM shellcast_unified.all_users GROUP BY state;

-- Find user by email across all states:
-- SELECT * FROM shellcast_unified.all_users WHERE email = 'user@example.com';

-- Find users with text notifications enabled:
-- SELECT * FROM shellcast_unified.all_users WHERE text_pref = 1 AND text_consent = 1;

-- ============================================================================
-- Testing Automatic Sync
-- ============================================================================
-- To verify that changes are automatically reflected:
--
-- 1. Make a change in source table:
--    UPDATE shellcast_nc.users SET email = 'newemail@example.com' WHERE id = 1;
--
-- 2. Query the view immediately:
--    SELECT * FROM shellcast_unified.all_users WHERE state = 'NC' AND id = 1;
--
-- 3. The change will be visible immediately - no sync needed!
-- ============================================================================
