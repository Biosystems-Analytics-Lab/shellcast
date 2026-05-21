# 6. Troubleshooting web apps

> **Doc 6 of 7** · [← 5. Development](05-DEVELOPMENT.md) · [Index](README.md) · [Next: 7. Web reference →](07-WEB_REFERENCE.md)

Symptoms when running or deploying `shellcast-web-{nc,sc,fl}`.

## Deploy / runtime

| Symptom | Things to check |
|---------|------------------|
| **502 Bad Gateway** on GAE | Deployed from **inside** app dir? `gunicorn -b :$PORT main:app` in `app.yaml`? Run `gunicorn -b :8080 main:app` locally — [04-DEPLOY_GAE.md](04-DEPLOY_GAE.md) |
| App crashes at startup | Cloud Logging traceback; missing env vars in `.env` / `app.yaml` vs `env.template` |
| **Host validation failed** (400) | `TRUSTED_HOSTS` in `main.py`; Bandwidth callback `Host` header — [04-DEPLOY_GAE.md](04-DEPLOY_GAE.md) |

## Database

| Symptom | Things to check |
|---------|------------------|
| Cannot connect locally | Cloud SQL proxy running; `DB_HOST`/`DB_PORT` or Unix socket path |
| Works locally, fails on GAE | `SQLALCHEMY` / socket URI for production; instance connection name |
| Map empty / no probabilities | **Analysis** ran and `SAVE_TO_DB=true`; correct state database — [analysis/08-TROUBLESHOOTING.md](../analysis/08-TROUBLESHOOTING.md) |

## Authentication

| Symptom | Things to check |
|---------|------------------|
| Sign-in fails locally | `GOOGLE_APPLICATION_CREDENTIALS` points to valid Firebase Admin JSON |
| Works on GAE, not local | Service account file and Firebase project match `ncsu-shellcast` |

## Notifications

| Symptom | Things to check |
|---------|------------------|
| No SMS | NC cron deployed; `NC_ORCHESTRATOR_SECRET` on NC/FL/SC; Bandwidth callback URL on NC — [03-NOTIFICATIONS.md](03-NOTIFICATIONS.md) |
| FL/SC SMS not in `notification_events` | FL/SC `NC_LOG_URL` and `NC_LOG_SECRET` set |
| Email unsubscribe 404 | Deploy app with `/u/<token>`; NC/SC/FL all have route in current repo |
| Unsubscribe works but user still emailed | Analysis still has `email_pref=1`; web only sets pref — [analysis/06-NOTIFICATIONS_ANALYSIS.md](../analysis/06-NOTIFICATIONS_ANALYSIS.md) |
| No forecast **email** | **Analysis** Gmail and `ENABLE_NOTIFICATIONS`, not web |

## Development environment

| Symptom | Things to check |
|---------|------------------|
| `ModuleNotFoundError` | Wrong venv; `pip install -r requirements.txt` from correct app |
| Unix socket errors on Windows | Use TCP proxy + `DB_HOST=127.0.0.1` — [01-GETTING_STARTED.md](01-GETTING_STARTED.md) |

## Getting help

- GAE logs: Cloud Console → Logging
- [07-WEB_REFERENCE.md](07-WEB_REFERENCE.md) §7 — contacts and issue trackers

## Related

- [04-DEPLOY_GAE.md](04-DEPLOY_GAE.md)
- [05-development/COMMANDS.md](05-development/COMMANDS.md)
