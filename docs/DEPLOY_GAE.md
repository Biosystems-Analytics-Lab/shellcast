# Deploy to Google App Engine

**You must deploy from inside each app's directory** so that `main.py` and `app.yaml` are at the application root. Deploying from `web/` with paths like `shellcast-web-nc/app.yaml` uses `web/` as the root, so GAE cannot find `main.py` and returns 502.

**Deploy NC first** (FL and SC depend on NC for callbacks and logging).

## Check before deploying (no GAE deploy)

You can confirm the app will start on GAE **without deploying** by running the same command GAE runs, locally:

```bash
cd web/shellcast-web-nc   # or shellcast-web-fl, shellcast-web-sc
# Use the same env as GAE (e.g. .env with required vars, or export from app.yaml)
gunicorn -b :8080 main:app
```

- If it **starts** and you can open http://localhost:8080 with no crash, the entrypoint and `main:app` are correct; GAE should not 502 for that reason.
- If it **crashes** (import error, missing env var, Firebase/DB error), you see the traceback locally and can fix before any deploy.

Requires: `pip install -r requirements.txt` and env vars (e.g. `.env` or same as in `app.yaml`). Stop with Ctrl+C.

## Using .env on GAE

On GAE the app loads environment variables from a **.env file if one is deployed**; that file overrides `env_variables` from `app.yaml`. To use .env in production:

1. Keep a `.env` in the app directory with the same variable names as in `app.yaml` (or `env.template`), and **do not** list `.env` in that app's `.gcloudignore`.
2. Deploy as usual; the uploaded `.env` will be read at startup and take precedence over `app.yaml`.

If `.env` is in `.gcloudignore` (or missing), GAE uses only `app.yaml` `env_variables`. Keep `.env` out of version control (e.g. in `.gitignore`) so secrets are not committed.

### "Host validation failed" (400 Bad Request)

Flask/Werkzeug checks the request `Host` header against `TRUSTED_HOSTS`. This can be triggered by:

- **Browser/GAE**: Hosts like `ncsu-shellcast.appspot.com` or version URLs (e.g. `staging-dot-default-dot-ncsu-shellcast.appspot.com`). The apps allow `.appspot.com`, `localhost`, and `127.0.0.1`.
- **Webhooks**: Incoming callbacks (e.g. **Bandwidth** → `/api/bandwidth/callback`) are sent by the provider's servers. If that provider sends a `Host` header that doesn't match `TRUSTED_HOSTS`, you get "Host validation failed". NC also forwards callbacks to FL/SC at `shellcast-fl-dot-...appspot.com`; those use `.appspot.com` and are already allowed.

If a webhook still fails: in Cloud Logging, find the failing request and check the `Host` (or `X-Forwarded-Host`) header. Add that value (or a pattern like `.provider.com`) to `TRUSTED_HOSTS` in `main.py`. As a last resort you can set `TRUSTED_HOSTS = None` to allow any host (weaker security).

## Prerequisites

- `gcloud` CLI installed and logged in: `gcloud auth login`
- Project set: `gcloud config set project ncsu-shellcast` (or your project ID)
- App Engine application created in the project (first-time: `gcloud app create` if prompted)

## Test deployment before committing (no traffic)

Deploy a **new version without sending traffic** so you can test it on a version URL before promoting:

```bash
cd web/shellcast-web-nc
# Deploy; new version gets a URL but receives 0% traffic
gcloud app deploy app.yaml cron.yaml --no-promote -v staging
```

After deploy, the CLI prints the version URL, e.g.:

`https://staging-dot-default-dot-ncsu-shellcast.appspot.com`

Open that URL and verify the app. When satisfied, either:

- **Promote this version to 100% traffic:**
  ```bash
  gcloud app services set-traffic default --splits=staging=1
  ```
- Or commit, then deploy again **with** promote (omit `--no-promote`) to make this the live version.

Use any version ID for `-v` (e.g. `staging`, `test-1`, or omit `-v` to get an auto-generated ID).

## Deploy commands (promote to live)

From the **repository root** (or from `web/`), run deploy from **inside** each app directory:

```bash
cd web/shellcast-web-nc
gcloud app deploy app.yaml cron.yaml --quiet

cd ../shellcast-web-fl
gcloud app deploy app.yaml --quiet

cd ../shellcast-web-sc
gcloud app deploy app.yaml --quiet
```

Only **NC** has and deploys `cron.yaml` (SMS is orchestrated by NC). FL and SC have no `cron.yaml` file.

Or in one line from repo root:

```bash
cd web/shellcast-web-nc && gcloud app deploy app.yaml cron.yaml --quiet && cd ../shellcast-web-fl && gcloud app deploy app.yaml --quiet && cd ../shellcast-web-sc && gcloud app deploy app.yaml --quiet
```

## After deploy – verify

1. **Homepage / login**
   - NC: https://shellcast-nc-dot-ncsu-shellcast.appspot.com/
   - FL: https://shellcast-fl-dot-ncsu-shellcast.appspot.com/
   - SC: https://shellcast-sc-dot-ncsu-shellcast.appspot.com/

2. **Bandwidth callback (NC only)**
   In Bandwidth dashboard, callback URL should be:
   `https://shellcast-nc-dot-ncsu-shellcast.appspot.com/api/bandwidth/callback`

3. **Cron**
   - GAE Console → App Engine → Cron jobs: you should see one job per service (NC, FL, SC) for `/send-bandwidth-message` at 07:00 America/New_York.

4. **Smoke test (optional)**
   - Log in on each site, open Preferences, toggle notification prefs, save.
   - If you have a smoke-test endpoint, call it to confirm SMS path.

## Cron and default service

NC's cron uses `target: default`. Ensure the **default service** in your GAE project is NC (the one that receives the Bandwidth callback), so the daily `/send-bandwidth-message` job runs on NC. Inbound SMS for FL and SC are not affected by cron target (they are forwarded from NC's callback).

## Why GAE deploy fails with 502

A **502 Bad Gateway** means GAE could not get a valid response from your app. Common causes:

| Cause | What happens | Fix |
|-------|----------------|-----|
| **Wrong deploy directory** | You ran `gcloud app deploy` from repo root or `web/`. GAE's app root is then wrong and it looks for `main.py` in the wrong place. | Always `cd web/shellcast-web-nc` (or FL/SC) first, then run `gcloud app deploy app.yaml cron.yaml`. |
| **App crashes on startup** | The process exits before handling requests (import error, missing env var, Firebase/DB error). GAE sees the process die → 502. | Run locally: `gunicorn -b :8080 main:app` in the app dir with the same env as GAE. Fix any traceback. Check **Cloud Logging** (below) for the exact error. |
| **Wrong or missing entrypoint** | GAE doesn't start a proper WSGI server or can't find `main:app`. | In **app.yaml** use: `entrypoint: gunicorn -b :$PORT main:app`. In **requirements.txt** include `gunicorn>=21.0.0`. |
| **Missing required env vars** | `create_app()` raises if required vars (e.g. `DB_USER`, `SECRET_KEY`) are missing. | Set them in **app.yaml** `env_variables` (or in a deployed `.env`). Match names to `env.template` / `main.py` `required_vars`. |

**Find the real error:** In **Google Cloud Console → Logging → Logs Explorer**, filter by resource type **App Engine application** and severity **Error**. The traceback (e.g. `ValueError: Missing required environment variables`, `ModuleNotFoundError`, or DB/Firebase errors) tells you what to fix.
