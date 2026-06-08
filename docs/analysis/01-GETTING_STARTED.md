# 1. Getting started with ShellCast analysis

> **Doc 1 of 9** · [Index](README.md) · [Next: 2. Configuration →](02-CONFIGURATION.md)

This guide walks through a **first successful run** of `shellcast-analysis` on your machine. For daily cron on the production iMac, see [05-DAILY_OPERATIONS.md](05-DAILY_OPERATIONS.md).

## Prerequisites

- **Operating system:** **macOS** or **Linux** — these are what this documentation and the production cron host assume. **Production** runs on a dedicated **macOS** iMac.

  **Windows** is not ruled out, but it is **not** the supported path in these guides. Much of the stack was chosen for Unix-like environments:

  - Daily runs use **`analysis_run.sh`** and (for Florida) **`xmrg_proc.sh`** — POSIX shell scripts, not PowerShell.
  - **Scheduling** on production uses **cron**; on Windows you would use Task Scheduler or WSL cron instead.
  - **External tools** (wgrib2, optional **cnvgrib** / NCEPLIBS-grib_util, **CDO**, GDAL) are documented here with macOS/Homebrew-style install notes; building or packaging them on native Windows is often more work than on macOS/Linux.
  - **Python** dependencies such as **pygrib** usually need **eccodes** (or legacy grib-api) installed on the system; that is straightforward on many Linux/macOS setups and can be fiddly on Windows unless you use **WSL2** (Linux inside Windows), which is the most practical way to run this analysis on a Windows PC if you need to.

  If you develop on Windows, plan extra time for tool installs and path configuration, or use WSL2 and follow the Linux-oriented steps where they apply.
- MySQL client libraries (for Cloud SQL via proxy)
- [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/mysql/sql-proxy)
- Python 3 with ability to install [pygrib](https://pypi.org/project/pygrib/) (often needs eccodes/grib API)
- **wgrib2** on `PATH` or configured in code for your OS
- For **Florida only**: CDO, `cnvgrib` (see [09-ANALYSIS.md](09-ANALYSIS.md) §4.7–4.8)

## 1. Get the repository

- **Contributing code:** fork [Biosystems-Analytics-Lab/shellcast](https://github.com/Biosystems-Analytics-Lab/shellcast), clone your fork, add `upstream`, and install pre-commit — [GETTING_STARTED.md](../../GETTING_STARTED.md#contributors-fork-remotes-and-pre-commit).
- **Local run only:** clone the lab repo directly — [GETTING_STARTED.md](../../GETTING_STARTED.md#run-locally-clone-and-setup).

Then enter the analysis tree:

```bash
cd shellcast/analysis/shellcast-analysis
```

## 2. Create local config (not in Git)

These files are **gitignored** — they exist only on each machine:

```bash
cp analysis_settings.template.ini analysis_settings.ini
cp analysis_paths.template.sh analysis_paths.sh
```

Edit them for your environment. See [02-CONFIGURATION.md](02-CONFIGURATION.md) for every section.

**Production:** keep `SAVE_TO_DB = true` and `ENABLE_NOTIFICATIONS` as needed. Repo clones used only for dev may use `SAVE_TO_DB = false`.

## 3. Python virtual environment

From `analysis/` (parent of `shellcast-analysis/`):

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Point `analysis_paths.sh` `VENV_ACTIVATE_PATH` at this venv's `bin/activate`.

## 4. Cloud SQL proxy

Download `cloud-sql-proxy` to the parent `analysis/` directory (see [09-ANALYSIS.md](09-ANALYSIS.md) §4.3).

In one terminal:

```bash
./cloud-sql-proxy --port 3306 your-project:region:instance-name
```

Match `HOST` / `PORT` in `analysis_settings.ini` `[gcp.mysql]` (typically `127.0.0.1:3306`).

## 5. Secrets and credentials (machine-local)

| File | Purpose |
|------|---------|
| `analysis_settings.ini` | DB, state shapefile names, notification flags |
| `analysis_paths.sh` | Paths to proxy, venv, main scripts |
| `gmail-api-desktop-credentials.json` | Gmail OAuth client (gitignored) |
| `gmail-api-token.json` | Gmail OAuth token after first auth (gitignored) |
| `encryption.key` | Fernet key for notification crypto (gitignored) |

Gmail setup: [06-NOTIFICATIONS_ANALYSIS.md](06-NOTIFICATIONS_ANALYSIS.md).

## 6. Input data

Spatial inputs must exist under `data/pqpf/{nc,sc,fl}/inputs/` before PQPF runs. **Documenting how to create/update those datasets is separate** — see [04-DATA_PREP_README.md](04-DATA_PREP_README.md) and your input-data documentation.

Florida may optionally refresh inputs from GCS at run time (`get_input_files()` in `fl_pqpf`).

## 7. Smoke test — one state

With proxy running and venv active:

```bash
cd analysis/shellcast-analysis
source analysis_paths.sh   # if paths are defined there
source "$VENV_ACTIVATE_PATH"
python nc_main.py
```

Check:

- Console / `../logs/nc/info.log` for errors
- Cloud SQL `shellcast_nc.cmu_probabilities` has rows for today (if `SAVE_TO_DB = true`)

Repeat with `sc_main.py` or `fl_main.py` when inputs for that state are ready. FL also runs XMRG processing first inside `fl_main.py`.

## 8. Full pipeline

```bash
chmod +x analysis_run.sh
./analysis_run.sh
```

This runs NC → SC → FL in sequence, then sends email per state if enabled in `analysis_settings.ini`.

## Next steps

- [03-STATE_GUIDES.md](03-STATE_GUIDES.md) — per-state differences
- [07-DEVELOPMENT.md](07-DEVELOPMENT.md) — changing code and deploying
- [08-TROUBLESHOOTING.md](08-TROUBLESHOOTING.md) — common failures
