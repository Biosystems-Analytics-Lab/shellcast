# 5. Web development tasks

> **Doc 5 of 7** · [← 4. Deploy GAE](04-DEPLOY_GAE.md) · [Index](README.md) · [Next: 6. Troubleshooting →](06-TROUBLESHOOTING.md)

Common tasks after [01-GETTING_STARTED.md](01-GETTING_STARTED.md). For exhaustive step-by-step history, see [07-WEB_REFERENCE.md](07-WEB_REFERENCE.md) §4–6.

## Run locally

1. Activate venv, start Cloud SQL proxy (TCP or Unix socket).
2. `cd web/shellcast-web-{nc,sc,fl}`
3. Ensure `.env` is populated.
4. `python main.py` → open `http://localhost:<PORT>` (NC default often **3361**).

Pre-deploy sanity check (same as GAE):

```bash
gunicorn -b :8080 main:app
```

See [04-DEPLOY_GAE.md](04-DEPLOY_GAE.md).

## Change environment variables

| Environment | Where |
|-------------|--------|
| Local | `.env` in the app directory (overrides `app.yaml` when `load_dotenv(override=True)` runs) |
| GAE | `app.yaml` `env_variables` and/or deployed `.env` (if not in `.gcloudignore`) |

After changing `EMAIL_SECRET_KEY`, update **analysis** `analysis_settings.ini` for that state and redeploy **both** analysis (if needed) and web.

## Database during development

- **TCP:** proxy on port 3306, `DB_HOST=127.0.0.1` in `.env`.
- **Unix socket:** `cloudsql/` under the app dir, proxy `--unix-socket` — matches production GAE pattern ([07-WEB_REFERENCE.md](07-WEB_REFERENCE.md) §4.5).

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
