# Deploy to Google App Engine

Deploy each service from its own directory. **Deploy NC first** (FL and SC depend on NC for callbacks and logging).

## Prerequisites

- `gcloud` CLI installed and logged in: `gcloud auth login`
- Project set: `gcloud config set project ncsu-shellcast` (or your project ID)
- App Engine application created in the project (first-time: `gcloud app create` if prompted)

## Deploy commands

From the `web/` directory:

```bash
# 1. Deploy NC first (Bandwidth callback and logging live here)
gcloud app deploy shellcast-web-nc/app.yaml shellcast-web-nc/cron.yaml --quiet

# 2. Deploy FL
gcloud app deploy shellcast-web-fl/app.yaml shellcast-web-fl/cron.yaml --quiet

# 3. Deploy SC
gcloud app deploy shellcast-web-sc/app.yaml shellcast-web-sc/cron.yaml --quiet
```

Or from each app directory:

```bash
cd shellcast-web-nc && gcloud app deploy app.yaml cron.yaml --quiet && cd ..
cd shellcast-web-fl && gcloud app deploy app.yaml cron.yaml --quiet && cd ..
cd shellcast-web-sc && gcloud app deploy app.yaml cron.yaml --quiet && cd ..
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
