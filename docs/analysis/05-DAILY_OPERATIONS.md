# 5. Daily operations (production analysis)

> **Doc 5 of 9** · [← 4. Data prep](04-DATA_PREP_README.md) · [Index](README.md) · [Next: 6. Notifications →](06-NOTIFICATIONS_ANALYSIS.md)

ShellCast forecast analysis normally runs on a **dedicated Mac (iMac)** via **cron**, not on Google App Engine.

## What runs each morning

1. `analysis_run.sh` starts Cloud SQL proxy in the background
2. Activates the Python venv from `analysis_paths.sh`
3. Runs `python nc_main.py` → `sc_main.py` → `fl_main.py`
4. Each main script:
   - Runs PQPF (and FL: XMRG + PQPF)
   - Optionally writes probabilities to Cloud SQL (`SAVE_TO_DB`)
   - Optionally sends user emails (`ENABLE_NOTIFICATIONS`)

Typical cron (Eastern time):

```cron
40 6 * * * /path/to/shellcast-analysis/analysis_run.sh >> ~/Desktop/cron.log 2>&1
```

See [09-ANALYSIS.md](09-ANALYSIS.md) §5 for `chmod +x`, Full Disk Access, and file permissions.

## What success looks like

| Check | Where |
|-------|--------|
| Script exits without error | `cron.log` or terminal |
| Today's PQPF GRIBs downloaded | `data/pqpf/raw/` |
| State logs clean | `analysis/logs/{nc,sc,fl}/info.log` |
| DB has today's probabilities | `cmu_probabilities` with `DATE(created) = CURDATE()` per state DB |
| Emails sent (if enabled) | Gmail sent folder; `notification_log` table (NC/FL; SC if table exists) |

## Logs

| Path | Content |
|------|---------|
| `analysis/logs/nc/info.log` | NC informational |
| `analysis/logs/nc/error.log` | NC errors |
| Same for `sc/`, `fl/` | |

Logging is configured in `setup_logging.py` (runs at start of each `*_main.py`).

## Production config reminders

On the analysis server, **never replace** from Git:

- `analysis_settings.ini` — must keep `SAVE_TO_DB = true` for production
- `analysis_paths.sh` — machine-specific paths
- `gmail-api-token.json`, `encryption.key`

After `git pull`, only **tracked Python** changes apply. See [07-DEVELOPMENT.md](07-DEVELOPMENT.md).

## Deploying code updates

1. Backup the analysis directory (or at least `analysis_settings.ini`, `analysis_paths.sh`, and tokens)
2. `git pull` on the production clone
3. Confirm ignored files unchanged
4. Run one state manually before relying on cron
5. Deploy web app changes if notification/unsubscribe behavior changed — [06-NOTIFICATIONS_ANALYSIS.md](06-NOTIFICATIONS_ANALYSIS.md)

## When not to wait for cron

- After changing input shapefiles (see your input-data documentation)
- After changing `analysis_settings.ini` database or shapefile names
- After Gmail or `EMAIL_SECRET_KEY` rotation
- After PQPF schedule outages at NOAA

## Related

- [01-GETTING_STARTED.md](01-GETTING_STARTED.md) — first-time setup
- [08-TROUBLESHOOTING.md](08-TROUBLESHOOTING.md) — failures
