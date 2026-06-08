# 5. Web development tasks

> **Doc 5 of 7** · [← 4. Deploy GAE](04-DEPLOY_GAE.md) · [Index](README.md) · [Next: 6. Troubleshooting →](06-TROUBLESHOOTING.md)

Common tasks after [01-GETTING_STARTED.md](01-GETTING_STARTED.md). For exhaustive step-by-step history, see [07-WEB_REFERENCE.md](07-WEB_REFERENCE.md) §4–6.

## Run locally

Follow [01-GETTING_STARTED.md](01-GETTING_STARTED.md): venv → Cloud SQL proxy → `.env` → OpenLayers build → `python main.py`.

Pre-deploy sanity check (same as GAE):

```bash
gunicorn -b :8080 main:app
```

See [04-DEPLOY_GAE.md](04-DEPLOY_GAE.md).

## Change environment variables

| Environment | Where |
|-------------|--------|
| Local | `.env` in the app directory (loaded via `python-dotenv`) |
| GAE | `app.yaml` `env_variables` and/or deployed `.env` (if not in `.gcloudignore`) |

After changing `EMAIL_SECRET_KEY`, update **analysis** `analysis_settings.ini` for that state and redeploy **both** analysis (if needed) and web.

## Database during development

- Start `./my-cloud-sql-proxy.sh web` from repo root (Unix socket at `/tmp/shellcast-csql/`).
- In `.env`: `DB_UNIX_SOCKET_PATH_PREFIX=/tmp/shellcast-csql/` and `CLOUD_SQL_INSTANCE_NAME=...`
- On GAE: `/cloudsql/` is mounted by App Engine — no local folder to create ([01-GETTING_STARTED.md](01-GETTING_STARTED.md) §4).

## OpenLayers

Map pages require `static/lib/ol.js` and `ol.css`. Build from `web/shellcast-web-nc` with `npm install && npm run build` (**OpenLayers 9.2.4**). See [01-GETTING_STARTED.md](01-GETTING_STARTED.md) §5.

## Deploy

Always from **inside** `web/shellcast-web-nc` (or sc/fl):

```bash
gcloud app deploy app.yaml cron.yaml   # NC only for cron.yaml
```

**NC first.** Details: [04-DEPLOY_GAE.md](04-DEPLOY_GAE.md), commands: [05-development/COMMANDS.md](05-development/COMMANDS.md).

## Clean up GAE versions and staging

Free-tier limits on service versions and staging bucket size. Delete old versions in Cloud Console; clean staging images when rollback is not needed.

```bash
gsutil -m rm "gs://staging.ncsu-shellcast.appspot.com/**"
```

See [05-development/COMMANDS.md](05-development/COMMANDS.md) and [07-WEB_REFERENCE.md](07-WEB_REFERENCE.md) §5.4.

## Git: push changes

After you commit locally, push to the team repository on GitHub (you need write access):

```bash
git push origin main
```

Use your branch name instead of `main` if your team works on branches. See [GETTING_STARTED.md](../../GETTING_STARTED.md) for clone and pre-commit setup.

## Tests

Unit tests under each app's `tests/` are **out of date** in places. See [07-WEB_REFERENCE.md](07-WEB_REFERENCE.md) §6 before relying on CI.

## When you change notifications

| Change | Also update |
|--------|-------------|
| Unsubscribe URL or token logic | All three web apps if behavior should match; `EMAIL_SECRET_KEY` in analysis |
| SMS send or Bandwidth tag | NC cron + FL/SC orchestrator endpoints; [03-NOTIFICATIONS.md](03-NOTIFICATIONS.md) |
| Forecast email content | **Analysis** `notifications.py`, not web |

## Development reference (subsections)

Longer or planning-oriented material lives in separate files under **`05-development/`** (same doc number, split for readability — a common pattern in numbered doc sets).

| Subsection file | Use when |
|-----------------|----------|
| [TODOs.md](05-development/TODOs.md) | High-level ideas for merging NC/SC/FL into one app |
| [CONSOLIDATION_INVENTORY.md](05-development/CONSOLIDATION_INVENTORY.md) | Comparing routes, templates, and JS/CSS across state apps before a refactor |
| [SCRIPTS_README.md](05-development/SCRIPTS_README.md) | Running helper scripts under repo `scripts/` (staging cleanup, deploy helpers) |
| [COMMANDS.md](05-development/COMMANDS.md) | `gcloud`, Cloud SQL proxy, staging cleanup command cheat sheet |

## Related

- [06-TROUBLESHOOTING.md](06-TROUBLESHOOTING.md)
