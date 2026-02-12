# Notifications

## Email

### Gmail API

#### Create access credentials

[Create access credentials](https://developers.google.com/workspace/guides/create-credentials#desktop-app)

To send notifications to users, the server requires impersonating a user. Physically interacting with authentication processes is not possible in this case. Therefore, automatic authentication should be implemented.

In order to do this, two options are available: "OAuth client ID credentials" and "Service account credentials". For the "Service account credentials," domain-wide configurations are required, which require administrative privileges to setup. For this reason, ShellCast uses "OAuth client ID credentials". Email notifications are sent from the ShellCast Analysis server that does not have a web server setup, so follow the "Desktop app" instructions on the "Create access credentials" link.

#### Generating Email Secret Key
*Currently, email notifications are being sent from the analysis server as a temporary measure to prevent redundant updates on the NC, SC, and FL websites, optimizing time efficiency. However, the email notification functionality should ultimately be implemented on the web server.*

**Option 1: Run the script**
```bash
cd analysis/shellcast-analysis
python src/generate_secret_key.py
```
**Option 2: One-liner**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## SMS (Bandwidth) – centralized logging in NC

All SMS notification events (NC, FL, SC) are logged in the **NC** database table `notification_events`. Bandwidth has a single callback URL pointing at the NC app; NC forwards callbacks to FL/SC when needed.

- **NC**
  - Set `NC_LOG_SECRET` (shared secret for the log-event endpoint).
  - Callback handles delivery status for all states and forwards inbound to FL and SC.

- **FL and SC**
  - Set `NC_LOG_URL` (NC app base URL, e.g. `https://shellcast-web-nc-dot-<project>.appspot.com`).
  - Set `NC_LOG_SECRET` (same value as NC).
  - FL/SC call NC’s `/api/bandwidth/log-event` to record outbound sends and inbound STOP/START.

### SMS cron orchestrator (single cron on NC)

Only the **NC** app has a GAE cron job for SMS. NC runs its own send, then triggers FL and SC by HTTP (POST to each app’s `/send_bandwidth_message`). FL and SC have no cron entries for SMS; they are invoked by NC.

- **NC**
  - Set `NC_ORCHESTRATOR_SECRET` (shared secret NC sends when calling FL/SC).
  - Cron handler calls FL and SC with header `X-NC-Orchestrator-Secret`.

- **FL and SC**
  - Set `NC_ORCHESTRATOR_SECRET` (same value as NC).
  - The `/send_bandwidth_message` endpoint accepts either GAE cron (header `X-Appengine-Cron`) or NC orchestrator (header `X-NC-Orchestrator-Secret`).

### Testing the Bandwidth callback

**NC (direct callback)**
Bandwidth hits NC at `/api/bandwidth/callback`. To test locally (replace port if NC runs elsewhere, e.g. 8080):

```bash
curl -X POST http://localhost:8080/api/bandwidth/callback \
  -H 'Content-Type: application/json' \
  -d '[
        {
          "type": "message-received",
          "message": {
            "id": "test-nc-1",
            "from": "+19842207351",
            "text": "START"
          }
        }
      ]'
```

**FL and SC (internal forward)**
To simulate NC forwarding a callback to FL or SC locally, POST to that app’s internal callback URL with the `X-Forwarded-By` header (replace port if the app runs elsewhere, e.g. 3361 for SC):

```bash
curl -X POST http://localhost:3361/api/bandwidth/callback/internal \
  -H 'Content-Type: application/json' \
  -H 'X-Forwarded-By: nc-callback-router' \
  -d '[
        {
          "type": "message-received",
          "message": {
            "id": "test-stop-fl-2",
            "from": "+19842207351",
            "text": "START"
          }
        }
      ]'
```

Use `"text": "START"` or `"text": "STOP"` to test opt-in/opt-out behavior.

**Why no row in `notification_events` for FL/SC?**

1. **Env vars** – FL and SC only POST to NC when `NC_LOG_URL` and `NC_LOG_SECRET` are set (e.g. in `.env`). If either is missing, inbound/outbound SMS are not logged to `notification_events`. Add them from each app’s `env.template` for local testing; point `NC_LOG_URL` at your running NC app (e.g. `http://localhost:8080`).
2. **User must exist** – Inbound STOP/START are only logged when the message’s phone number exists in that state’s `users` table. For a test like the one above, ensure the number (e.g. `+19842207351`) is present in the FL or SC `users` table so a row is written.
