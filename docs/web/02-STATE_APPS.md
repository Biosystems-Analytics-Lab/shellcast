# 2. State web apps (NC, SC, FL)

> **Doc 2 of 7** · [← 1. Getting started](01-GETTING_STARTED.md) · [Index](README.md) · [Next: 3. Notifications →](03-NOTIFICATIONS.md)

ShellCast runs **three separate Flask applications** on Google App Engine. They share patterns (map, preferences, Firebase auth) but use **different databases** and some **different routes**.

## Comparison

| | North Carolina | South Carolina | Florida |
|--|----------------|----------------|---------|
| **Directory** | `web/shellcast-web-nc` | `web/shellcast-web-sc` | `web/shellcast-web-fl` |
| **Database** | `shellcast_nc` | `shellcast_sc` | `shellcast_fl` |
| **Deploy `cron.yaml`** | Yes (SMS + orchestration) | No | No |
| **Bandwidth callback URL** | NC only (primary) | Via NC forward | Via NC forward |
| **SMS send trigger** | GAE cron on NC; NC HTTP-calls FL/SC | NC orchestrator → `/send-bandwidth-message` | NC orchestrator → `/send_bandwidth_message` |
| **Email unsubscribe** | `GET /u/<token>` | `GET /u/<token>` | `GET /u/<token>` |
| **Forecast email sending** | Analysis (`nc_main.py`) | Analysis (`sc_main.py`) | Analysis (`fl_main.py`) |

## Production URLs (typical)

Verify in your GAE console — service names may differ:

| State | URL pattern |
|-------|-------------|
| NC | `https://ncsu-shellcast.appspot.com` or `https://shellcast-nc-dot-ncsu-shellcast.appspot.com` |
| SC | `https://shellcast-sc-dot-ncsu-shellcast.appspot.com` |
| FL | `https://shellcast-fl-dot-ncsu-shellcast.appspot.com` |

`EMAIL_SECRET_KEY` in each app's environment must match the same state's `[*.Notification]` section in analysis `analysis_settings.ini` so unsubscribe links work ([03-NOTIFICATIONS.md](03-NOTIFICATIONS.md)).

## Why three apps instead of one

The project began with **NC only**. **SC** and **FL** were added by **duplicating** the NC web tree and editing state-specific content, thresholds, and integrations. That minimized time-to-launch but increases maintenance when fixing bugs or adding features three times.

Possible future directions (not commitments):

- Single app with state routing — see [05-development/TODOs.md](05-development/TODOs.md) and [05-development/CONSOLIDATION_INVENTORY.md](05-development/CONSOLIDATION_INVENTORY.md)
- Move forecast email back to web — discussed in [analysis/06-NOTIFICATIONS_ANALYSIS.md](../analysis/06-NOTIFICATIONS_ANALYSIS.md)

## Deploy order

**Deploy NC first.** FL and SC depend on NC for Bandwidth callbacks, centralized SMS logging, and the daily SMS orchestrator. See [04-DEPLOY_GAE.md](04-DEPLOY_GAE.md).

## Code layout (each app)

| Path | Purpose |
|------|---------|
| `main.py` | Flask app factory, Firebase, DB URI |
| `app.yaml` | GAE runtime, env vars, entrypoint |
| `routes/pages.py` | HTML pages (map, preferences, `/u/<token>`) |
| `routes/api.py` | JSON API for map data and user prefs |
| `routes/cron.py` | Cron handlers (NC: SMS; FL/SC: orchestrated send) |
| `models/` | SQLAlchemy models |
| `templates/`, `static/` | UI |
| `env.template` | Copy to `.env` for local dev |

## Related

- [03-NOTIFICATIONS.md](03-NOTIFICATIONS.md) — SMS architecture
- [analysis/03-STATE_GUIDES.md](../analysis/03-STATE_GUIDES.md) — analysis-side state differences
- [07-WEB_REFERENCE.md](07-WEB_REFERENCE.md) — code structure detail
