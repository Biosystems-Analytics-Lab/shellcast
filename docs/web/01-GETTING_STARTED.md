# 1. Getting started (local web development)

> **Doc 1 of 7** · [Index](README.md) · [Next: 2. State apps →](02-STATE_APPS.md)

This guide is for **developers** who want to run one state app on their machine. For project context without installing code, see the repository [README.md](../../README.md).

## Prerequisites

- **macOS or Linux** recommended (Unix socket paths and deploy docs assume this; Windows may work with TCP-only DB access — see [07-WEB_REFERENCE.md](07-WEB_REFERENCE.md))
- Python 3 compatible with [App Engine supported versions](https://cloud.google.com/appengine/docs/standard/python3/runtime)
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud`)
- [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/mysql/sql-proxy)
- Access to ShellCast secrets (DB password, Firebase service account, Bandwidth keys) from a project administrator

## 1. Get the repository

- **Contributing code:** fork [Biosystems-Analytics-Lab/shellcast](https://github.com/Biosystems-Analytics-Lab/shellcast), clone your fork, add `upstream`, and install pre-commit — [GETTING_STARTED.md](../../GETTING_STARTED.md#contributors-fork-remotes-and-pre-commit).
- **Local run only:** `git clone https://github.com/Biosystems-Analytics-Lab/shellcast.git` — [GETTING_STARTED.md](../../GETTING_STARTED.md#run-locally-clone-and-setup).

Use a **shallow path** if possible — very long paths can break Unix socket paths for Cloud SQL.

## 2. Pick a state app

```bash
cd web/shellcast-web-nc   # or shellcast-web-sc / shellcast-web-fl
```

Each state is a **separate** Flask app with its own `.env` and database name (`shellcast_nc`, `shellcast_sc`, `shellcast_fl`).

## 3. Python virtual environment

From `web/` (or repo root, if you prefer one venv per developer):

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r shellcast-web-nc/requirements.txt
pip install -r shellcast-web-nc/requirements-test.txt   # optional, for tests
```

Repeat `pip install` paths if you work on multiple state apps (requirements are usually aligned).

## 4. Environment file (`.env`)

```bash
cd web/shellcast-web-nc
cp env.template .env
```

Edit `.env` with real values. **Never commit `.env`.** Required variables are enforced at startup in `main.py` (see `env.template` for names).

Important groups:

| Group | Examples |
|-------|----------|
| Flask | `SECRET_KEY`, `EMAIL_SECRET_KEY` (must match analysis for unsubscribe — [03-NOTIFICATIONS.md](03-NOTIFICATIONS.md)) |
| Database | `DB_USER`, `DB_PASS`, `DB_NAME`, `DB_HOST` / `DB_PORT` for local TCP |
| Cloud SQL socket | `DB_UNIX_SOCKET_PATH_PREFIX`, `CLOUD_SQL_INSTANCE_NAME` when using Unix socket |
| Firebase | Set `GOOGLE_APPLICATION_CREDENTIALS` to your service account JSON path |

Legacy note: older docs refer to `config.py` from `config-template.py`. Current apps load **`.env`** via `python-dotenv`. See [07-WEB_REFERENCE.md](07-WEB_REFERENCE.md) §4.5–4.6 if you still use `config.py` on an old machine.

## 5. Cloud SQL proxy

**TCP (simplest for first try):**

```bash
# from repo root or where cloud-sql-proxy lives
./cloud-sql-proxy --port 3306 ncsu-shellcast:us-east1:ncsu-shellcast-database
```

In `.env`, use `DB_HOST=127.0.0.1` and `DB_PORT=3306`.

**Unix socket (closer to GAE):** create `web/shellcast-web-nc/cloudsql/` with permissive mode, run proxy with `--unix-socket` — [07-WEB_REFERENCE.md](07-WEB_REFERENCE.md) §4.5.

## 6. Firebase (local sign-in)

1. Download a Firebase Admin SDK key from the Firebase console (service account).
2. `export GOOGLE_APPLICATION_CREDENTIALS="/path/to/firebase-admin-sdk-credentials.json"`

See [07-WEB_REFERENCE.md](07-WEB_REFERENCE.md) §4.7.

## 7. Run the app

With venv active and proxy running:

```bash
cd web/shellcast-web-nc
python main.py
```

Open the URL shown in the console (NC often uses port **3361** — check `PORT` in `.env`).

**Smoke check:** home/map loads, sign-in works, Preferences page opens.

## 8. Next steps

| Task | Doc |
|------|-----|
| NC vs SC vs FL differences | [02-STATE_APPS.md](02-STATE_APPS.md) |
| Deploy to production | [04-DEPLOY_GAE.md](04-DEPLOY_GAE.md) |
| SMS / email split | [03-NOTIFICATIONS.md](03-NOTIFICATIONS.md) |
| Problems | [06-TROUBLESHOOTING.md](06-TROUBLESHOOTING.md) |
