# 1. Getting started (local web development)

> **Doc 1 of 7** · [Index](README.md) · [Next: 2. State apps →](02-STATE_APPS.md)

This guide is for **developers** setting up a state web app locally. For project context without installing code, see the repository [README.md](../../README.md).

## Prerequisites

- **macOS or Linux** recommended (Unix socket paths and deploy docs assume this)
- **Python 3** compatible with [App Engine supported versions](https://cloud.google.com/appengine/docs/standard/python3/runtime)
- **Node.js and npm** (for OpenLayers map assets — see [§5](#5-openlayers-map-assets))
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud`) — optional for local run; required for deploy
- Access to ShellCast secrets (DB password, Firebase service account, Bandwidth keys) from a project administrator

## Pick a state app

```bash
cd web/shellcast-web-nc   # or shellcast-web-sc / shellcast-web-fl
```

Each state is a **separate** Flask app with its own `.env`, `app.yaml`, and database name (`shellcast_nc`, `shellcast_sc`, `shellcast_fl`).

---

## Setup checklist

| Step | What | Local | Deployed (GAE) |
|------|------|-------|----------------|
| 1 | [Python virtual environment](#1-python-virtual-environment) | `web/venv/` | GAE runtime |
| 2 | [Cloud SQL Auth Proxy](#2-cloud-sql-auth-proxy) | `web/cloud-sql-proxy` | Not used (GAE mounts `/cloudsql/`) |
| 3 | [`.env`](#3-environment-file-env) | Secrets + local socket path | Optional; usually `app.yaml` only |
| 4 | [`app.yaml`](#4-appyaml-for-deployment) | Not used locally | Production config |
| 5 | [OpenLayers](#5-openlayers-map-assets) | `static/lib/ol.js` + `ol.css` | Same files in deploy bundle |

Then: [Firebase](#6-firebase-local-sign-in) → [Run the app](#7-run-the-app).

---

## 1. Python virtual environment

One shared venv under `web/` is enough for all state apps:

```bash
cd web
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r shellcast-web-nc/requirements.txt
pip install -r shellcast-web-nc/requirements-test.txt   # optional, for tests
```

NC, SC, and FL requirements are aligned; installing from NC covers the others. **`python-dotenv`** is required so `.env` is loaded at startup.

---

## 2. Cloud SQL Auth Proxy

Web local development uses a **Unix socket** (same connection style as GAE). Analysis uses a **separate** proxy binary and TCP — see [docs/analysis/01-GETTING_STARTED.md](../analysis/01-GETTING_STARTED.md).

### Download binaries (once per machine)

From the **repository root**:

```bash
sh cloud-sql-proxy-setup.sh
```

This installs:

| Binary | Purpose |
|--------|---------|
| `analysis/cloud-sql-proxy` | Analysis server / cron (TCP port 3306) |
| `web/cloud-sql-proxy` | Local web dev (Unix socket) |

It also creates `/tmp/shellcast-csql/` (short path for macOS socket length limits).

Create your local proxy script from the template (gitignored — do not commit the real connection name):

```bash
cp my-cloud-sql-proxy.template.sh my-cloud-sql-proxy.sh
# Edit instance_connection_name (Cloud Console → SQL → Connection name)
chmod +x my-cloud-sql-proxy.sh
```

### Start the proxy for web dev

From the **repository root** (do **not** use `source`):

```bash
./my-cloud-sql-proxy.sh web
```

Leave this terminal running. The socket file appears under `/tmp/shellcast-csql/` with a filename matching your **Connection name** (for example `your-project:region:instance-name`).

---

## 3. Environment file (`.env`)

```bash
cd web/shellcast-web-nc   # or sc / fl
cp env.template .env
```

Edit `.env` with real values from a project administrator. **Never commit `.env`.**

### Required groups

| Group | Variables | Notes |
|-------|-----------|-------|
| Flask | `SECRET_KEY`, `EMAIL_SECRET_KEY`, `HOST`, `PORT` | `EMAIL_SECRET_KEY` must match analysis for unsubscribe — [03-NOTIFICATIONS.md](03-NOTIFICATIONS.md) |
| Database | `DB_USER`, `DB_PASS`, `DB_NAME` | Per-state DB name |
| Cloud SQL (local) | `DB_UNIX_SOCKET_PATH_PREFIX`, `CLOUD_SQL_INSTANCE_NAME` | Use `/tmp/shellcast-csql/` locally (see `env.template`) |
| SQLAlchemy pool | `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE` | Defaults in template |

Example local Cloud SQL settings (must match `./my-cloud-sql-proxy.sh web` and your Cloud SQL **Connection name** from the GCP console):

```bash
DB_UNIX_SOCKET_PATH_PREFIX=/tmp/shellcast-csql/
CLOUD_SQL_INSTANCE_NAME=your-project:region:instance-name
```

On **GAE**, the app uses `/cloudsql/` — that path is set in `app.yaml`, not `.env`, unless you deploy a `.env` file intentionally ([04-DEPLOY_GAE.md](04-DEPLOY_GAE.md)).

### Firebase (local)

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/firebase-admin-sdk-credentials.json"
```

See [07-WEB_REFERENCE.md](07-WEB_REFERENCE.md) §4.7.

---

## 4. `app.yaml` for deployment

`app.yaml` holds **production** settings for Google App Engine. It is **gitignored** (secrets); use `app.yaml.template` as a starting point or copy from a project administrator.

```bash
cd web/shellcast-web-fl   # example
cp app.yaml.template app.yaml
# Edit with real secrets and service name
```

Important Cloud SQL settings for GAE (you do **not** create this folder — GAE mounts it):

```yaml
env_variables:
  DB_UNIX_SOCKET_PATH_PREFIX: "/cloudsql/"
  CLOUD_SQL_INSTANCE_NAME: "your-project:region:instance-name"
```

Also ensure the App Engine service is **linked to the Cloud SQL instance** in GCP (Console → App Engine → Settings → Cloud SQL connections). Deploy workflow: [04-DEPLOY_GAE.md](04-DEPLOY_GAE.md).

---

## 5. OpenLayers map assets

The map pages load OpenLayers from `static/lib/ol.js` and `static/lib/ol.css`. Those files are **built from npm**, not checked into git (`ol.js` is gitignored).

| Item | Value |
|------|-------|
| **Package** | [`ol`](https://www.npmjs.com/package/ol) |
| **Version** | **9.2.4** (pinned in `web/shellcast-web-nc/package.json` as `^9.2.4`) |
| **Build location** | `web/shellcast-web-nc/` only — one build serves all state apps |

### Build steps

Requires Node.js and npm.

```bash
cd web/shellcast-web-nc
npm install          # installs ol@9.2.4; postinstall runs build
npm run build        # copies ol.js + ol.css into static/lib/
```

The build script `scripts/copy-ol-to-static.js` copies only the files needed for deployment (not full `node_modules/`).

### Use in SC and FL

After building in NC, copy the artifacts to the other apps (or rebuild if you add a package.json there later):

```bash
cp static/lib/ol.js  ../shellcast-web-sc/static/lib/
cp static/lib/ol.css ../shellcast-web-sc/static/lib/
cp static/lib/ol.js  ../shellcast-web-fl/static/lib/
cp static/lib/ol.css ../shellcast-web-fl/static/lib/
```

### Verify

Reload the map page. If the browser console shows **`ol is not defined`**, `static/lib/ol.js` is missing — run `npm run build` again.

---

## 6. Firebase (local sign-in)

1. Download a Firebase Admin SDK key (service account) from the Firebase console.
2. `export GOOGLE_APPLICATION_CREDENTIALS="/path/to/firebase-admin-sdk-credentials.json"`

---

## 7. Run the app

Terminal 1 — proxy (repo root):

```bash
./my-cloud-sql-proxy.sh web
```

Terminal 2 — app:

```bash
cd web
source venv/bin/activate
cd shellcast-web-nc
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/firebase-admin-sdk-credentials.json"
python main.py
```

Open the URL in the console (NC often uses port **3361** — check `PORT` in `.env`).

**Smoke check:** home/map loads (OpenLayers), sign-in works, Preferences page opens.

**Pre-deploy check (matches GAE):** from the same app directory, run `gunicorn -b :8080 main:app`, open http://localhost:8080, then Ctrl+C. See [04-DEPLOY_GAE.md](04-DEPLOY_GAE.md) for what successful output looks like and how to interpret errors.

---

## Next steps

| Task | Doc |
|------|-----|
| NC vs SC vs FL differences | [02-STATE_APPS.md](02-STATE_APPS.md) |
| Deploy to production | [04-DEPLOY_GAE.md](04-DEPLOY_GAE.md) |
| SMS / email split | [03-NOTIFICATIONS.md](03-NOTIFICATIONS.md) |
| Command cheat sheet | [05-development/COMMANDS.md](05-development/COMMANDS.md) |
| Problems | [06-TROUBLESHOOTING.md](06-TROUBLESHOOTING.md) |
| Legacy long reference | [07-WEB_REFERENCE.md](07-WEB_REFERENCE.md) |
