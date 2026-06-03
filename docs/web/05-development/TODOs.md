# TODOs.md

> **05-DEVELOPMENT** subsection · [← 5. Development](../05-DEVELOPMENT.md) · [Index](../README.md)
> Context: [README.md](../README.md), [02-STATE_APPS.md](../02-STATE_APPS.md)

## Platform consolidation

NC, SC, and FL web sites to be one instead of having separate services for SC and FL.

1. Consolidate databases into one
2. API routes updates
3. Move email notification function from analysis server

## Email verification (not implemented)

Columns `users.email_verified` and `users.email_verified_at` exist in all state databases but no application flow sets or checks them yet.

- [ ] Decide verification approach (Firebase `emailVerified` sync vs. custom send-link flow)
- [ ] On successful verification: set `email_verified = true`, `email_verified_at = now`
- [ ] Gate email closure alerts on verified email (if required by policy), or surface status in preferences UI
- [ ] Reset verification when user changes email address on preferences
- [ ] Expose `email_verified` on `GET /user-info` if the UI should show status

See also `TODO(email-verification)` on `User` models in each state web app.

## Database cleanup (soft-deleted users and leases)

Web **Delete account** only sets `users.deleted = true` and clears PII (email, phone, Firebase UID — see [What is PII?](../../DATABASE_STORED_PROCEDURES.md#what-is-pii)); it does **not** `DELETE` the MySQL row. Soft-deleted `user_leases` behave the same way.

- [ ] Add a **cron job** (per state DB) to purge soft-deleted rows after a documented retention period (`users.deleted = 1`, `user_leases.deleted = 1`) — implement as `DELETE` statements and/or new procedures in `shellcast_create_db_{nc,fl,sc}.sql`
- [ ] Log row counts and cutoff date each run; document retention in ops runbook

See [DATABASE_STORED_PROCEDURES.md](../../DATABASE_STORED_PROCEDURES.md#web-account-deletion-soft-delete-not-row-removal).

## Notification / schema follow-ups

- [ ] Wire `NotificationEvent.log_email()` (NC) so outbound emails are logged in `notification_events`
- [ ] Align FL/SC `POST /user-info` text opt-in/out timestamps with NC (preferences submit + SMS inbound)
- [ ] If you use `shellcast_unified.all_users`, recreate the view from `create_unified_users_view.sql` after schema changes (e.g. after `email_consent` was dropped from all state DBs)
