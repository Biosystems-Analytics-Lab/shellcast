# 6. Email notifications (analysis server)

> **Doc 6 of 9** · [← 5. Daily operations](05-DAILY_OPERATIONS.md) · [Index](README.md) · [Next: 7. Development →](07-DEVELOPMENT.md)

User **forecast emails** are sent from **`shellcast-analysis`** after each state's PQPF run completes. **SMS** is handled by the web apps — see [03-NOTIFICATIONS.md](../web/03-NOTIFICATIONS.md).

## Why email is sent from analysis (not web)

Early ShellCast put **all notification logic in the web app**, when analysis covered **North Carolina only**. As the project added **South Carolina** and then **Florida**, the team copied the NC web pattern for speed. Each state app still shares most behavior but needs **state-specific** pieces (URLs, copy, thresholds, FL-only cases). Maintaining three near-duplicate codebases became tedious.

Sending **forecast emails from the analysis machine** (`src/notifications.py`, after each `*_main.py` run) was a practical way to **centralize** “who gets mail today” next to the data that was just written to Cloud SQL, without repeating the same pipeline in three web deployments.

That is a **historical engineering choice**, not a permanent rule. A future refactor could move email back into web (or a shared service) if that fits better—especially if notification rules and templates should live with user preferences in one place. Until then, this document describes what runs **today**: analysis sends Gmail; web handles unsubscribe and SMS.

## Architecture

| Step | Where |
|------|--------|
| Build recipient list + email HTML | `src/notifications.py` on analysis machine |
| Send via Gmail API | Same (`GmailServices`) |
| One-click unsubscribe | State **web** app `GET /u/<token>` |
| Opt-out in database | Web sets `email_pref = false` |

## When emails run

Each `*_main.py` ends with:

```python
notification_config = NotificationConfig(STATE)
if notification_config.notifications_enabled:
    EmailNotification(dir_config, notification_config, STATE, ...).send()
```

Controlled by `[NC.Notification]`, `[SC.Notification]`, `[FL.Notification]` → `ENABLE_NOTIFICATIONS` in `analysis_settings.ini`. See [02-CONFIGURATION.md](02-CONFIGURATION.md).

## Who receives email

Criteria in `user_wants_email_notifications()`:

1. `email_pref == 1` in Cloud SQL
2. Non-empty `email` address
3. Today's forecast meets user's `prob_pref` (category threshold)
4. User appears in `SelectUserLeaseProbsToday` (lease linked, today's `cmu_probabilities`) — procedure details: [DATABASE_STORED_PROCEDURES.md](../DATABASE_STORED_PROCEDURES.md)

Florida uses **1-day** probability only in the filter (`prob_only_today=True`). NC and SC consider 1-, 2-, and 3-day columns.

## Gmail setup (analysis machine)

1. Create Google Cloud **OAuth desktop** credentials — [Google credentials guide](https://developers.google.com/workspace/guides/create-credentials#desktop-app)
2. Save client JSON as `gmail-api-desktop-credentials.json` in `shellcast-analysis/` (gitignored)
3. First run opens browser to authorize; saves `gmail-api-token.json` (gitignored)
4. Set `EMAIL_SENDER` in `[Notification]`

Generate signing keys for unsubscribe tokens:

```bash
cd analysis/shellcast-analysis
python src/generate_secret_key.py
```

Or: `python -c "import secrets; print(secrets.token_hex(32))"`

## Unsubscribe links

Analysis embeds a signed link in each email:

```text
https://{state-web-base}/u/{token}
```

Token payload: `user_id`, `email`, timestamp; salt `email-unsubscribe`; max age 60 days.

**Secret keys must match:**

| Analysis `analysis_settings.ini` | GAE app |
|-----------------------|---------|
| `[NC.Notification] EMAIL_SECRET_KEY` | NC `EMAIL_SECRET_KEY` |
| `[SC.Notification] EMAIL_SECRET_KEY` | SC `EMAIL_SECRET_KEY` |
| `[FL.Notification] EMAIL_SECRET_KEY` | FL `EMAIL_SECRET_KEY` |

`NotificationConfig.secret_key` checks env `EMAIL_SECRET_KEY` first, then state section, then `[Notification] EMAIL_SECRET_KEY`.

### Web handlers (deploy with analysis changes)

| App | Route | File |
|-----|-------|------|
| NC | `/u/<token>` | `web/shellcast-web-nc/routes/pages.py` |
| SC | `/u/<token>` | `web/shellcast-web-sc/routes/pages.py` |
| FL | `/u/<token>` | `web/shellcast-web-fl/routes/pages.py` |

On success: `email_pref = false`, `email_opt_out_date` set, confirmation page `unsubscribed.html`.

## Notification logs

After sends, `NotificationLogManager` appends rows to `notification_log` via SQLAlchemy. NC and FL schemas include this table; confirm SC production DB has the table if you rely on logs there.

## Florida developer email

Separate from user alerts: `[FL.Developer]` `SEND_EMAIL_TO_DEVELOPER` sends CSV attachments via `DevEmailNotificationFL` in `fl_main.py`.

## Testing without cron

1. Set `ENABLE_NOTIFICATIONS = true` for one state
2. Ensure today's probabilities exist in DB (`SAVE_TO_DB = true` on a prior run)
3. Run single main: `python nc_main.py`
4. Check logs and `notification_log`

Use test addresses in DB or a dev database when possible.

## Related

- [02-CONFIGURATION.md](02-CONFIGURATION.md)
- [07-DEVELOPMENT.md](07-DEVELOPMENT.md) — deploy checklist
- [08-TROUBLESHOOTING.md](08-TROUBLESHOOTING.md) — no emails sent
