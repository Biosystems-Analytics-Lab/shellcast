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
- **wgrib2** on `PATH` (all states) — [§5](#5-wgrib2-nc-sc-fl)
- For **Florida only**: **wgrib2**, **CDO**, **`cnvgrib`**, **GDAL** — install via `setup-florida-dev.sh` in [§6](#6-florida-external-tools-wgrib2-cdo-cnvgrib-gdal)

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

**Prerequisite:** MySQL client libraries on your machine.

Download the [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/mysql/sql-proxy) to the parent `analysis/` directory (repo root also has helper scripts such as `cloud-sql-proxy-setup.sh`).

```bash
cd analysis
# download cloud-sql-proxy for your OS, then:
chmod +x ./cloud-sql-proxy
```

In one terminal (TCP — typical for analysis):

```bash
./cloud-sql-proxy --port 3306 your-project:region:instance-name
```

Match `HOST` / `PORT` in `analysis_settings.ini` `[gcp.mysql]` (typically `127.0.0.1:3306`). Stop the proxy with `Ctrl+C`.

## 5. wgrib2 (NC, SC, FL)

**wgrib2** crops CONUS PQPF GRIB2 files to each state's bounding box (`LON_WE` / `LAT_SN` in `analysis_settings.ini`). All three states need it before `pqpf_procs.py` can run. Florida's `xmrg_proc.sh` also calls `wgrib2 -small_grib` when building XMRG GeoTIFFs.

### 5.1 Prerequisites before `setup-florida-dev.sh`

Install these **before** running `./setup-florida-dev.sh` (the script checks for `git`, `make`, and `cc`; it can install `cmake` via Homebrew if missing):

| Tool | Why ShellCast needs it |
|------|-------------------------|
| **Xcode Command Line Tools** or **GCC** (`brew install gcc`) | [NOAA-EMC/wgrib2](https://github.com/NOAA-EMC/wgrib2) is compiled C code. The build needs a C compiler (`cc` / `clang` from Apple, or `gcc` from Homebrew). |
| **cmake** (`brew install cmake`) | Official wgrib2 build uses CMake (version 3.15+). |
| **make** | Runs the compile after CMake generates Makefiles. |
| **git** | Clones the wgrib2 source into `shellcast-analysis/wgrib2/`. |

**Do you need `brew install gcc` specifically?**

- **Often yes on macOS** if Command Line Tools are not installed, or if you want a newer compiler than the system default.
- ShellCast's setup script uses a **minimal** CMake build (`USE_G2CLIB=OFF`, `USE_NETCDF=OFF`). That build was tested with Apple's `cc` (clang) and does **not** require **gfortran** / a Fortran compiler.
- You **do** need gfortran (included in Homebrew `gcc`) only if you enable optional wgrib2 features (Fortran API, grid interpolation, etc.) — not required for PQPF crop or Florida XMRG.

```bash
# Typical macOS prep (once per machine)
xcode-select --install          # if CLT not already installed
brew install cmake gcc          # gcc optional if CLT cc works; cmake required if not installed
```

### 5.2 Install wgrib2

**Script (recommended):** from `analysis/shellcast-analysis/`:

```bash
./setup-florida-dev.sh --wgrib2
```

(No flags is the same as `--wgrib2`.) See [§6](#6-florida-external-tools-wgrib2-cdo-cnvgrib-gdal) for the full **Florida** toolchain (CDO, cnvgrib, GDAL) — install those **one flag at a time**, not with `--all`, on a first-time machine.

**Manual install:** follow [NOAA-EMC/wgrib2](https://github.com/NOAA-EMC/wgrib2) — official README and `cmake` / `make install` steps.

### 5.3 Build output vs command name (important)

Compiling wgrib2 produces a binary **inside the build tree**, not where ShellCast or cron look for it:

| Location | What it is |
|----------|------------|
| `wgrib2/build/src/wgrib2` | **Build artifact** after `make` — only for development; cron does not use this path. |
| `/usr/local/bin/wgrib2` | **Installed command** after `make install` (or `setup-florida-dev.sh`) — this is what you want. |

The runnable command name is **`wgrib2`** (not `wgrib2.exe`, not a `.sh` wrapper). `make install` may also place a legacy **`wgrib`** binary in the same `bin/` directory; ShellCast calls **`wgrib2`** only.

Verify after install:

```bash
/usr/local/bin/wgrib2
wgrib2 -version    # if /usr/local/bin is on your PATH
```

### 5.4 System-wide install and cron

Daily analysis runs under **cron** with a **minimal environment** (limited `PATH`, no your shell profile). External tools must be installed where code and scripts can find them without relying on a repo-relative build path.

| Caller | How it finds wgrib2 |
|--------|---------------------|
| **`pqpf_procs.py`** (NC/SC/FL PQPF crop) | On macOS (`Darwin`), hard-coded **`/usr/local/bin/wgrib2`**. On other OS types, `wgrib2` on `PATH`. |
| **`xmrg_proc.sh`** (Florida XMRG) | Command name `wgrib2` on `PATH`; script prepends `/usr/local/bin`. |

That is why `setup-florida-dev.sh` defaults to `INSTALL_PREFIX=/usr/local` and installs **`/usr/local/bin/wgrib2`**. A binary left only under `shellcast-analysis/wgrib2/build/src/` will work in an interactive terminal if you type the full path, but **cron and `pqpf_procs.py` will not find it**.

**Cron gotchas (macOS):** even with `/usr/local/bin/wgrib2` installed, subprocess calls from cron have failed in production until **Full Disk Access** was granted and the **full path** was used in Python — see [08-TROUBLESHOOTING.md](08-TROUBLESHOOTING.md) and [09-ANALYSIS.md](09-ANALYSIS.md) §5.

**Historical compile links** (may be outdated): [CPC wgrib2](https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/), [compile questions](https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/compile_questions.html).

## 6. Florida external tools (wgrib2, CDO, cnvgrib, GDAL)

You **cannot** run `fl_main.py` / `xmrg_proc.sh` without all four. NC and SC also need **wgrib2** (§5); Florida adds **CDO**, **`cnvgrib`**, and **GDAL** for the XMRG GIS pipeline.

For **what each tool does** in the pipeline, see [09-ANALYSIS.md](09-ANALYSIS.md) §4 and [03-STATE_GUIDES.md](03-STATE_GUIDES.md) (Florida flowcharts).

| Tool | Used for (Florida) | Installed by |
|------|-------------------|--------------|
| **wgrib2** | PQPF crop (`pqpf_procs.py`) and XMRG geographic crop (`xmrg_proc.sh`) | `--wgrib2` → `/usr/local/bin/wgrib2` |
| **cnvgrib** | Convert XMRG **GRIB1** → **GRIB2** | `--cnvgrib` → `ncep-lib-utils/nceplibs/bin/cnvgrib` |
| **CDO** | Merge hourly GRIB2, units, multi-day rain totals (`tp_24h.tif`, …) | `--brew-tools` → Homebrew `cdo` on `PATH` |
| **GDAL** | Reproject grids, write GeoTIFFs (`gdalwarp`) | `--brew-tools` → Homebrew `gdal` on `PATH` |

### 6.1 `setup-florida-dev.sh`

ShellCast ships one setup script for these tools:

```text
analysis/shellcast-analysis/setup-florida-dev.sh
```

Run it from `analysis/shellcast-analysis/` (or pass the full path from the repo root). List flags anytime:

```bash
cd analysis/shellcast-analysis
./setup-florida-dev.sh --help
```

The script can clone and compile **wgrib2**, `brew install` **CDO** and **GDAL**, and build **cnvgrib** via `ncep-lib-utils/ncep_lib_utils.sh`. Flags are **composable** (e.g. `--wgrib2 --brew-tools`).

### 6.2 Prerequisites (before running the script)

Install these **on the machine once** before the first `./setup-florida-dev.sh` run:

| Prerequisite | Required for | Notes |
|--------------|--------------|-------|
| **Homebrew** | `--brew-tools`, `--cnvgrib` | `brew` must be on `PATH`. |
| **Xcode Command Line Tools** (`xcode-select --install`) | `--wgrib2` | Provides `cc` / `make`. |
| **cmake** (`brew install cmake`) | `--wgrib2` | wgrib2 builds with CMake 3.15+. Script can `brew install cmake` if missing. |
| **git**, **make** | `--wgrib2`, `--cnvgrib` | Clone NOAA source repos. |
| **gcc** (`brew install gcc`) | `--cnvgrib` | Provides **gfortran** for NCEPLIBS; not needed for the minimal wgrib2 build (§5.1). |

```bash
# Typical one-time macOS prep
xcode-select --install
brew install cmake gcc    # gcc when you plan to run --cnvgrib
```

wgrib2-only (NC/SC/FL PQPF): §5.1 — Apple's `cc` is often enough; gfortran is **not** required for wgrib2.

### 6.3 Recommended install order (one step at a time)

**Do not use `--all` on a first-time setup.** That runs wgrib2, CDO/GDAL, and cnvgrib in one shot; if something fails, it is harder to see which step broke. Install and **verify each tool** before moving on.

Use `--all` only after the steps below work individually, or when reproducing a machine that is already known good.

From `analysis/shellcast-analysis/`:

**Step 1 — wgrib2**

```bash
./setup-florida-dev.sh --wgrib2
/usr/local/bin/wgrib2
wgrib2 -version
```

See §5.3–5.4 if cron or `pqpf_procs.py` cannot find the binary.

**Step 2 — CDO and GDAL**

```bash
./setup-florida-dev.sh --brew-tools
cdo -V
gdalwarp --version
```

`xmrg_proc.sh` prepends `/usr/local/bin` to `PATH`. If cron reports `cdo: command not found`, see [08-TROUBLESHOOTING.md](08-TROUBLESHOOTING.md).

**Step 3 — cnvgrib**

```bash
./setup-florida-dev.sh --cnvgrib
./ncep-lib-utils/nceplibs/bin/cnvgrib
```

The script installs Homebrew deps (`jasper`, `libpng`, `zlib`, `openblas`) and compiles NCEPLIBS. CMake needs **Jasper ≥ 2.0.25** — without it, configure fails with `Could NOT find Jasper`. Usage text (no arguments) means the binary is installed correctly.

### 6.4 Script flags and environment

| Flag | What it does |
|------|----------------|
| *(no flags)* | Same as `--wgrib2` |
| `--wgrib2` | Clone, build, install wgrib2 to `/usr/local/bin/wgrib2` |
| `--brew-tools` | `brew install cdo gdal` (+ cnvgrib build deps: jasper, libpng, zlib, openblas) |
| `--cnvgrib` | Build `ncep-lib-utils/nceplibs/bin/cnvgrib` (installs brew deps if needed) |
| `--all` | All of the above in one run — **avoid on first setup** (§6.3) |
| `--help` | Print usage |

Optional environment variables: `INSTALL_PREFIX` (default `/usr/local`), `WGRIB2_DIR`, `WGRIB2_TAG`, `JOBS`.

### 6.5 Tool reference (manual install)

Use these only if you are not using `setup-florida-dev.sh`.

**wgrib2** — §5; must be **`/usr/local/bin/wgrib2`** on macOS for cron and `pqpf_procs.py`.

**cnvgrib** — `xmrg_proc.sh` calls:

```text
ncep-lib-utils/nceplibs/bin/cnvgrib -g12 <input.grb> <output.grb>
```

Manual path: `ncep-lib-utils/ncep_lib_utils.sh` (clones NOAA-EMC libraries). ShellCast only needs the **`cnvgrib`** binary.

**CDO** — `brew install cdo` if not using `--brew-tools`.

**GDAL** — `brew install gdal` if not using `--brew-tools`.

## 7. Secrets and credentials (machine-local)

| File | Purpose |
|------|---------|
| `analysis_settings.ini` | DB, state shapefile names, notification flags |
| `analysis_paths.sh` | Paths to proxy, venv, main scripts |
| `gmail-api-desktop-credentials.json` | Gmail OAuth **client** JSON from Google Cloud (gitignored) |
| `gmail-api-token.json` | Gmail OAuth **token**, created after first browser sign-in (gitignored) |
| `encryption.key` | Fernet key that encrypts `gmail-api-token.json` at rest (gitignored) |

All three Gmail-related files live in **`analysis/shellcast-analysis/`** (same directory as `nc_main.py`). Point to them from `[Notification]` in `analysis_settings.ini`:

```ini
[Notification]
GMAIL_API_CREDENTIAL_FILE = gmail-api-desktop-credentials.json
GMAIL_API_TOKEN_FILE = gmail-api-token.json
EMAIL_SENDER = shellcastapp@ncsu.edu
```

Skip this section if you are only testing PQPF with `ENABLE_NOTIFICATIONS = false`. You need it before forecast emails can send.

### 7.1 `gmail-api-desktop-credentials.json` (OAuth client)

1. Open [Google Cloud Console](https://console.cloud.google.com/) for the ShellCast project (e.g. `ncsu-shellcast`).
2. **APIs & Services** → **Library** → enable **Gmail API**.
3. **APIs & Services** → **OAuth consent screen** — configure for your workspace/Google account (internal or external, as your org requires).
4. **APIs & Services** → **Credentials** → **Create credentials** → **OAuth client ID**.
5. Application type: **Desktop app**. Download the JSON.
6. Save it as `analysis/shellcast-analysis/gmail-api-desktop-credentials.json` (do not commit).

Official walkthrough: [Google — Create credentials (desktop app)](https://developers.google.com/workspace/guides/create-credentials#desktop-app).

### 7.2 `gmail-api-token.json` and `encryption.key` (first Gmail auth)

You do **not** create either file by hand. They appear the first time analysis completes Gmail OAuth. They serve different roles:

| File | Who creates it | What it holds |
|------|----------------|---------------|
| **`gmail-api-token.json`** | **Google** issues the token; **ShellCast** writes the file | OAuth **access** and **refresh** tokens (and related fields) returned after you sign in in the browser |
| **`encryption.key`** | **ShellCast only** (`Fernet.generate_key()` in `src/notifications.py`) | A local symmetric key used to **encrypt** the token file before it is saved on disk |

**What Google gives you vs what ShellCast stores**

After you approve access in the browser, Google's OAuth service returns credential JSON (access token, refresh token, expiry, etc.). ShellCast does **not** save that JSON as plain text. `GmailServices.get_authenticated_gmail_service()` passes it through `Cipher.encrypt_token_data()` and writes the **ciphertext** to `gmail-api-token.json`. On the next run, `Cipher.decrypt_token_data()` reads `encryption.key`, decrypts the file, and rebuilds the credentials (refreshing the access token when expired).

```
Browser sign-in (Google OAuth)
        →  plain token JSON from Google
        →  ShellCast encrypts with encryption.key (Fernet)
        →  gmail-api-token.json on disk (encrypted bytes, not readable JSON)
```

**Why `encryption.key` exists**

The refresh token in `gmail-api-token.json` is powerful: anyone with it can keep sending mail as `EMAIL_SENDER` until it is revoked. ShellCast keeps the token on the analysis iMac so cron can send email without a browser each morning. Encrypting at rest adds a layer of protection if someone copies the token file from disk — they still need `encryption.key` in the same directory to decrypt it. Google does not provide `encryption.key`; it is generated locally the first time encryption runs and reused for all future read/write of that token file.

**First-time setup steps**

1. Ensure `GMAIL_API_CREDENTIAL_FILE` and `GMAIL_API_TOKEN_FILE` are set in `analysis_settings.ini` (§7 above).
2. Set `ENABLE_NOTIFICATIONS = true` for at least one state in `[NC.Notification]` / `[SC.Notification]` / `[FL.Notification]`.
3. With venv active and Cloud SQL proxy running, run a main script that sends mail (e.g. `python nc_main.py` after today's data is in the DB), or any code path that calls `GmailServices.get_authenticated_gmail_service()`.
4. A **browser window** opens — sign in as the sender account (`EMAIL_SENDER`) and approve access.
5. On success, ShellCast creates **`encryption.key`** (if missing), then writes **`gmail-api-token.json`** (encrypted).

Cron and later runs decrypt the token, refresh it when needed, and send mail without opening a browser.

**Re-authenticate:** delete `gmail-api-token.json`, then run the OAuth step again. Keep the same `encryption.key` unless you intentionally rotate it (if you delete `encryption.key` without deleting the token file, the old token file can no longer be decrypted).

### 7.3 `EMAIL_SECRET_KEY` (unsubscribe links — not `encryption.key`)

Unsubscribe links in forecast emails use a **separate** signing key (`EMAIL_SECRET_KEY` in each `[NC.Notification]` / `[SC.Notification]` / `[FL.Notification]` section). It must match that state's GAE `EMAIL_SECRET_KEY`. Generate once:

```bash
cd analysis/shellcast-analysis
python src/generate_secret_key.py
# or: python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the value into `analysis_settings.ini` and the matching web app `.env` / `app.yaml`. Details: [06-NOTIFICATIONS_ANALYSIS.md](06-NOTIFICATIONS_ANALYSIS.md).

## 8. Input data

Spatial inputs must exist under `data/pqpf/{nc,sc,fl}/inputs/` before PQPF runs. **Documenting how to create/update those datasets is separate** — see [04-DATA_PREP_README.md](04-DATA_PREP_README.md) and your input-data documentation.

Florida may optionally refresh inputs from GCS at run time (`get_input_files()` in `fl_pqpf`).

## 9. Smoke test — one state

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

## 10. Full pipeline

```bash
chmod +x analysis_run.sh
./analysis_run.sh
```

This runs NC → SC → FL in sequence, then sends email per state if enabled in `analysis_settings.ini`.

## Next steps

- [03-STATE_GUIDES.md](03-STATE_GUIDES.md) — per-state differences
- [07-DEVELOPMENT.md](07-DEVELOPMENT.md) — changing code and deploying
- [08-TROUBLESHOOTING.md](08-TROUBLESHOOTING.md) — common failures
