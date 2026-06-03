# 7. Development and deployment

> **Doc 7 of 9** · [← 6. Notifications](06-NOTIFICATIONS_ANALYSIS.md) · [Index](README.md) · [Next: 8. Troubleshooting →](08-TROUBLESHOOTING.md)

How to change `shellcast-analysis` code safely and update the production analysis server.

## Repository workflow

Source code lives on [GitHub](https://github.com/Biosystems-Analytics-Lab/shellcast). Clone, commit, and pre-commit setup: [GETTING_STARTED.md](../../GETTING_STARTED.md).

## Where to change common behavior

| Goal | Location |
|------|----------|
| PQPF download / GRIB processing | `src/pqpf_procs.py`, `src/utils.py` |
| NC geospatial logic | `src/nc_pqpf/nc_pqpf.py` |
| SC zonal stats | `src/sc_pqpf/sc_pqpf.py` |
| FL seasons / accumulation | `src/fl_pqpf/fl_pqpf.py`, `src/fl_pqpf/tp_xmrg.py` |
| Email content / filtering | `src/notifications.py` |
| Notification config / URLs / secrets | `src/management.py`, `analysis_settings.ini` |
| DB connection strings | `src/utils.py` (`get_connection_string`) |
| Cron order / states run | `analysis_run.sh` |
| Shapefile names / bounds | `analysis_settings.ini` `[NC]` / `[SC]` / `[FL]` |

## Local development tips

- Use `SAVE_TO_DB = false` in dev `analysis_settings.ini` to avoid writing test data to production (use a dev database if available).
- Run **one state** at a time: `python nc_main.py`
- Logs: `analysis/logs/{state}/`
- Tests: `analysis/shellcast-analysis/run_tests.py`, `src/tests/test_email_notification.py`

## Deploying to the production analysis server

Production often lives outside the repo path (e.g. a copy under `Downloads/analysis/shellcast-analysis`). Typical process:

### 1. Backup

```bash
cp -a /path/to/shellcast-analysis /path/to/shellcast-analysis.backup-$(date +%Y%m%d)
```

Especially: `analysis_settings.ini`, `analysis_paths.sh`, `gmail-api-token.json`, `encryption.key`.

### 2. Pull code only

```bash
cd /path/to/shellcast   # git root
git pull
```

Or copy specific files from your dev clone:

- `src/**/*.py`
- `nc_main.py`, `sc_main.py`, `fl_main.py`
- `setup_logging.py`

### 3. Do not overwrite (gitignored)

| File | Why |
|------|-----|
| `analysis_settings.ini` | Production `SAVE_TO_DB`, DB passwords, keys |
| `analysis_paths.sh` | Machine paths |
| `gmail-api-*.json`, `encryption.key` | Auth |
| `data/` | GRIB cache and shapefiles |

`git pull` does not change gitignored files. Avoid `rsync` of the whole repo tree onto production.

### 4. Deploy web if notifications changed

If `notifications.py` or unsubscribe behavior changed, deploy the relevant **shellcast-web-{nc,sc,fl}** apps so `/u/<token>` and `EMAIL_SECRET_KEY` stay aligned. See [06-NOTIFICATIONS_ANALYSIS.md](06-NOTIFICATIONS_ANALYSIS.md).

### 5. Smoke test

```bash
source analysis_paths.sh && source "$VENV_ACTIVATE_PATH"
# proxy running in another terminal
python nc_main.py   # or sc / fl
```

Check logs and DB before the next cron.

## Changing notification rules

- **Recipients:** `filter_users_by_preferences()` and `user_wants_email_notifications()` in `notifications.py`
- **Email body:** `NotificationEmailContentGenerator` in same file
- **Unsubscribe:** `_generate_unsubscribe_link()` (analysis) + web `one_click_unsubscribe` (each state)

Update `src/tests/test_email_notification.py` when filter logic changes.

## Changing database schema

SQL reference scripts: `analysis/shellcast-analysis/db_scripts/`. Apply changes to Cloud SQL deliberately; update stored procedures if notification queries change. See [DATABASE.md](../DATABASE.md) and [DATABASE_STORED_PROCEDURES.md](../DATABASE_STORED_PROCEDURES.md) (which procedures are used, unused, and state-specific).

## Related

- [05-DAILY_OPERATIONS.md](05-DAILY_OPERATIONS.md)
- [01-GETTING_STARTED.md](01-GETTING_STARTED.md)
- [08-TROUBLESHOOTING.md](08-TROUBLESHOOTING.md)
