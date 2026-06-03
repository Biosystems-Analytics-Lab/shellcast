# 2. Analysis configuration

> **Doc 2 of 9** · [← 1. Getting started](01-GETTING_STARTED.md) · [Index](README.md) · [Next: 3. State guides →](03-STATE_GUIDES.md)

ShellCast analysis uses **two local files** with different jobs:

| File | Used by | Contains |
|------|---------|----------|
| **`analysis_settings.ini`** | Python (`nc_main.py`, `src/*`) | Databases, shapefile names, notification flags, optional GCP bucket name (FL) |
| **`analysis_paths.sh`** | Shell (`analysis_run.sh` / cron) | Paths to Cloud SQL proxy, venv, and `*_main.py` scripts |

Python does not read `analysis_paths.sh`. The cron wrapper does not read `analysis_settings.ini`. That split avoids mixing INI settings with shell-only paths.

Both runtime files are **gitignored**. Copy from the tracked templates:

```bash
cp analysis_settings.template.ini analysis_settings.ini
cp analysis_paths.template.sh analysis_paths.sh
```

Legacy names `config.ini` / `config.sh` are still gitignored if present on older machines; migrate to the names above.

## Files on each machine

| File | In Git? | Purpose |
|------|---------|---------|
| `analysis_settings.template.ini` | Yes | Template for Python settings |
| `analysis_settings.ini` | **No** | Runtime Python settings |
| `analysis_paths.template.sh` | Yes | Template for shell paths |
| `analysis_paths.sh` | **No** | Runtime paths for cron |
| `gmail-api-desktop-credentials.json` | **No** | Gmail OAuth client |
| `gmail-api-token.json` | **No** | Gmail OAuth token |
| `encryption.key` | **No** | Fernet key |
| `data/` | **No** | GRIB, inputs, outputs |

## analysis_paths.sh

Sourced by `analysis_run.sh` before starting the proxy and Python:

| Variable | Typical value |
|----------|----------------|
| `CLOUD_SQL_PATH` | `../cloud-sql-proxy` (parent of `shellcast-analysis`) |
| `CLOUD_SQL_INSTANCE_NAME` | `ncsu-shellcast:us-east1:ncsu-shellcast-database` |
| `VENV_ACTIVATE_PATH` | `../venv/bin/activate` |
| `NC_MAIN_PY` / `SC_MAIN_PY` / `FL_MAIN_PY` | Absolute paths to `*_main.py` |

## analysis_settings.ini sections

### `[NC]`, `[SC]`, `[FL]`

Per-state PQPF settings:

- `DB_NAME` — MySQL database (`shellcast_nc`, `shellcast_sc`, `shellcast_fl`)
- `LEASE_SHP`, `CMU_SHP` (NC) — shapefile names under `data/pqpf/{state}/inputs/`
- Column names for lease ID, CMU, rain thresholds
- `LON_WE`, `LAT_SN` — wgrib2 subset bounds (e.g. `-79:-75`, `33:37`)
- `THRESHOLD` — SC rain threshold for zonal stats

### `[gcp.mysql]`

Cloud SQL credentials (via proxy):

```ini
DB_USER = ...
DB_PASS = ...
HOST = 127.0.0.1
PORT = 3306
```

### `[gcp.bucket]` (Florida — optional)

```ini
BUCKET_NAME = shellcast_data_bucket1
```

This section is used only when **Florida** calls `get_input_files()` in `pqpf_procs.py`, which can download lease/SHA-related files from Google Cloud Storage into `data/pqpf/fl/inputs/` before the PQPF run.

**Original intent:** FDACS updates lease and related spatial data on a periodic schedule. The Florida **data prep** pipeline (`data_prep/fl/`) was meant to automate fetching those sources, processing them, and uploading results to a bucket so the analysis machine could pull fresh inputs without manual copy steps.

**What happened in practice:** Source URLs and attribute/field names from the upstream data can change without notice, so the automated prep-and-upload path did not stay reliable. Treat the bucket workflow as a **historical example**, not a requirement for running ShellCast.

**Recommended approach:** Keep Florida spatial inputs **locally** under `data/pqpf/fl/inputs/`, the same way North Carolina and South Carolina use `data/pqpf/nc/inputs/` and `data/pqpf/sc/inputs/`. Update shapefiles manually (or with your own process) when organizations publish new boundaries. If you do not use bucket download, ensure `get_input_files()` is not called (or is commented out) in your `fl_pqpf` flow so the run does not depend on GCS credentials or bucket contents.

See [04-DATA_PREP_README.md](04-DATA_PREP_README.md) for the ArcPy/bucket upload side; see input-data documentation for file names and layout.

### `[Notification]`

Shared email settings:

| Key | Purpose |
|-----|---------|
| `GMAIL_API_CREDENTIAL_FILE` | OAuth client JSON filename (in `shellcast-analysis/`) |
| `GMAIL_API_TOKEN_FILE` | Saved token after first Gmail auth |
| `DB_STORED_PROCEDURE` | Usually `SelectUserLeaseProbsToday` (see [DATABASE_STORED_PROCEDURES.md](../DATABASE_STORED_PROCEDURES.md)) |
| `EMAIL_SENDER` | From address (e.g. `shellcastapp@ncsu.edu`) |
| `EMAIL_SECRET_KEY` | Fallback signing key for unsubscribe tokens |

### `[NC.Notification]`, `[SC.Notification]`, `[FL.Notification]`

| Key | Purpose |
|-----|---------|
| `ENABLE_NOTIFICATIONS` | `true` / `false` — run email after PQPF |
| `EMAIL_SECRET_KEY` | Per-state key; must match that state's GAE `EMAIL_SECRET_KEY` for unsubscribe links |

Read by `NotificationConfig` in `src/management.py`.

### `[FL.Developer]`

| Key | Purpose |
|-----|---------|
| `EMAIL_RECEIVER` | Comma-separated dev addresses |
| `SEND_EMAIL_TO_DEVELOPER` | Send FL diagnostic email with CSV attachments |

### `[NC.SaveToDB]`, `[SC.SaveToDB]`, `[FL.SaveToDB]`

| Key | Purpose |
|-----|---------|
| `SAVE_TO_DB` | `true` — write today's probabilities to Cloud SQL |

**Production must use `true`.** If `false`, stored procedure returns no users for notifications and the public map has no new forecast.

## Environment variables

| Variable | Used for |
|----------|----------|
| `EMAIL_SECRET_KEY` | Overrides config file secret for token signing (optional) |
| `SHELLCAST_TOKEN_KEY` | Referenced in config as encryption env name for some crypto paths |

## Web base URLs (code, not INI)

Unsubscribe links use state URLs from `NotificationConfig.web_base_url`:

| State | URL |
|-------|-----|
| NC | `https://ncsu-shellcast.appspot.com` |
| SC | `https://shellcast-sc-dot-ncsu-shellcast.appspot.com` |
| FL | `https://shellcast-fl-dot-ncsu-shellcast.appspot.com` |

## Related

- [01-GETTING_STARTED.md](01-GETTING_STARTED.md)
- [06-NOTIFICATIONS_ANALYSIS.md](06-NOTIFICATIONS_ANALYSIS.md)
- [DATABASE.md](../DATABASE.md)
