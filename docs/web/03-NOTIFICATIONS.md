# 3. Notifications (web)

> **Doc 3 of 7** · [← 2. State apps](02-STATE_APPS.md) · [Index](README.md) · [Next: 4. Deploy GAE →](04-DEPLOY_GAE.md)

ShellCast splits notifications between **analysis** (forecast email) and **web** (SMS, unsubscribe pages). This document focuses on **web** behavior.

## Email vs SMS — who does what

| Channel | Sent from | Document |
|---------|-----------|----------|
| **Forecast email** (morning closure probabilities) | `analysis/shellcast-analysis` (Gmail API) | [analysis/06-NOTIFICATIONS_ANALYSIS.md](../analysis/06-NOTIFICATIONS_ANALYSIS.md) |
| **Email unsubscribe** (`/u/<token>` in email links) | Each state **web** app | This doc + [02-STATE_APPS.md](02-STATE_APPS.md) |
| **SMS** (Bandwidth) | **Web** — NC cron orchestrates NC, FL, SC | Below |

### Why email is not sent from web

Originally all notification logic lived in the **NC web app**. Adding **SC** and **FL** by duplicating that codebase made it costly to maintain three copies. **Forecast emails** were implemented on the **analysis server** to centralize sending next to the daily database update. That is a practical choice, not a permanent architecture rule — see background in [analysis/06-NOTIFICATIONS_ANALYSIS.md](../analysis/06-NOTIFICATIONS_ANALYSIS.md).

### Email secret key (unsubscribe links)

Web and analysis must share the same `EMAIL_SECRET_KEY` per state so tokens in email links validate on `GET /u/<token>`.

**Generate a key:**

```bash
cd analysis/shellcast-analysis
python src/generate_secret_key.py
# or: python -c "import secrets; print(secrets.token_hex(32))"
```

Set in:

- Web: `.env` / `app.yaml` for each `shellcast-web-{state}`
- Analysis: `[NC.Notification]` / `[SC.Notification]` / `[FL.Notification]` in `analysis_settings.ini`

Gmail API credentials for **sending** mail live on the **analysis** machine only — [analysis/06-NOTIFICATIONS_ANALYSIS.md](../analysis/06-NOTIFICATIONS_ANALYSIS.md).

## SMS (Bandwidth) – centralized logging in NC

All SMS notification events (NC, FL, SC) are logged in the **NC** database table `notification_events`. Bandwidth has a single callback URL pointing at the NC app; NC forwards callbacks to FL/SC when needed.

### How each state sends SMS (NC, FL, SC) and uses Bandwidth tags

Each state app sends SMS through a shared Bandwidth helper that **always sets the Bandwidth `tag` field to the two-letter state code** (`'NC'`, `'FL'`, or `'SC'`). This `tag` is what NC uses in the callback handler to know which state an event belongs to.

#### Outbound SMS sending workflow (per state, with `tag`)

```
┌─ NC cron (GAE) ─────────────────────────────────────────────────────────────┐
│  hits NC /send-bandwidth-message                                            │
└──────────┬──────────────────────────────────────────────────────────────────┘
           ▼
   NC notification_preprocess_sms()   (choose NC users to notify)
           ▼
   NC _send_bandwidth_message_bulk(users_to_notify)
           ▼
   send_sms_batch(..., state='NC')  →  Bandwidth MessageRequest(tag='NC')
           ▼
   Bandwidth delivers SMS to NC users


┌─ NC cron orchestrator ──────────────────────────────────────────────────────┐
│  inside NC /send-bandwidth-message:                                         │
│    _trigger_state_send('FL') and _trigger_state_send('SC')                  │
└──────────┬───────────────────────────────┬──────────────────────────────────┘
           │ POST /send-bandwidth-message  │ POST /send-bandwidth-message
           │ (FL app)                      │ (SC app)
           ▼                               ▼
   FL notification_preprocess_sms()   SC notification_preprocess_sms()
           ▼                               ▼
   FL _send_bandwidth_message_bulk()  SC _send_bandwidth_message_bulk()
           ▼                               ▼
   send_sms_batch(..., state='FL')    send_sms_batch(..., state='SC')
     → Bandwidth MessageRequest(        → Bandwidth MessageRequest(
         tag='FL' )                       tag='SC' )
           ▼                               ▼
   Bandwidth delivers SMS to FL users  Bandwidth delivers SMS to SC users
           │                               │
           └─► FL/SC log outbound to NC via /api/bandwidth/log-event (state, message_id)
```

- **Shared Bandwidth helper (per app, same pattern in NC/FL/SC)**
  - `core/notifications/bandwidth_send.py`:
    - `send_sms_single(to_number, text, state)` – builds a `MessageRequest` with `tag=state`.
    - `send_sms_batch(users_to_notify, text, state, ...)` – loops over users and sends with `tag=state`.
  - Example (NC, but FL/SC are identical):

```python
message_request = bandwidth.MessageRequest(
    application_id=bw_application_id,
    to=[phone_number],
    var_from=bw_from_number,
    text=text,
    tag=state,  # 'NC', 'FL', or 'SC' – used by NC callback router
)
```

- **NC app (shellcast-web-nc)**
  - Cron endpoint: `/send-bandwidth-message` (in `routes/cron.py`).
  - Flow:
    - `notification_preprocess_sms()` selects NC users to notify.
    - `_send_bandwidth_message_bulk(users_to_notify)` calls `send_sms_batch(..., state='NC', ...)`, so **every NC SMS has `tag='NC'`**.
    - For each `(user_id, phone_number, success, message_id)`:
      - Logs outbound directly in NC DB via `NotificationEvent.log_sms_outbound(...)` with `state='NC'` and `message_id`.

- **FL app (shellcast-web-fl)**
  - HTTP-triggered cron endpoint: `/send-bandwidth-message` (in `routes/cron.py`), invoked by NC’s orchestrator.
  - Flow:
    - `notification_preprocess_sms()` selects FL users to notify.
    - `_send_bandwidth_message_bulk(...)` calls `send_sms_batch(..., state='FL', ...)`, so **every FL SMS has `tag='FL'`**.
    - For each successful send:
      - Calls NC’s `/api/bandwidth/log-event` via `_log_sms_to_nc(...)` with `state='FL'`, `direction='outbound'`, and `message_id`.

- **SC app (shellcast-web-sc)**
  - HTTP-triggered cron endpoint: `/send-bandwidth-message` (in `routes/cron.py`), invoked by NC’s orchestrator.
  - Flow:
    - `notification_preprocess_sms()` selects SC users to notify.
    - `_send_bandwidth_message_bulk(...)` calls `send_sms_batch(..., state='SC', ...)`, so **every SC SMS has `tag='SC'`**.
    - For each successful send:
      - Calls NC’s `/api/bandwidth/log-event` via `_log_sms_to_nc(...)` with `state='SC'`, `direction='outbound'`, and `message_id`.

**How `tag` is used on the callback side**

- When Bandwidth sends a callback to NC at `/api/bandwidth/callback`, each event includes the same `tag` that was set when the message was sent.
- NC reads `tag = event.get("tag", "")` and:
  - Uses it to know which state the outbound SMS came from (NC/FL/SC).
  - For **delivery/failed** events where `tag` is `FL` or `SC`, forwards the event to that state’s `/api/bandwidth/callback/internal`.
  - For **inbound** events, handles NC users locally and then forwards to FL/SC as needed (see flow chart below).

### Bandwidth callback workflow (single URL → NC, orchestration to FL/SC)

Because only one callback URL can be registered with Bandwidth, that URL is the **NC** app. NC receives every callback, then routes or forwards as needed.

```
┌─ User ──────────────────────────────────────────────────────────────────────┐
│  • Receives: closure alerts, STOP/START confirmations, HELP reply (SMS)      │
│  • Sends: STOP, START, HELP (SMS)                                            │
└───────┬─────────────────────────────────────────────────────────────────────┘
        │ User sends SMS (STOP / START / HELP)
        ▼
┌─ Bandwidth ─────────────────────────────────────────────────────────────────┐
│  • Receives user’s SMS → forwards to single callback URL (NC only)           │
│  • Delivers outbound SMS from NC/FL/SC → user (alerts, confirmations)        │
└───────────────────────────────────────────┬─────────────────────────────────┘
                                            │ POST all events (delivery, failed, message-received)
                                            ▼
┌─ NC (shellcast-web-nc) ─────────────────────────────────────────────────────┐
│  /api/bandwidth/callback                                                    │
│       │                                                                      │
│       ├─► Parse event type + tag (NC/FL/SC)                                  │
│       │                                                                      │
│       ├─► message-delivered / message-failed:                               │
│       │      • Update delivery status in NC notification_events             │
│       │      • If tag = FL or SC → POST event to that app’s                 │
│       │        /api/bandwidth/callback/internal                              │
│       │                                                                      │
│       └─► message-received (inbound from user):                             │
│              • Handle STOP/START/HELP for NC users (log to NC DB)            │
│              • POST same event to FL and SC internal                         │
│                                                                              │
│  /api/bandwidth/log-event  ◄── FL and SC POST here to log inbound/outbound  │
└───────┬─────────────────────────────────┬──────────────────────────────────┘
        │ POST /callback/internal         │ POST /callback/internal
        │ (X-Forwarded-By: nc-callback-router)
        ▼                                 ▼
┌─ FL (shellcast-web-fl) ──────────────┐   ┌─ SC (shellcast-web-sc) ───────────┐
│  /api/bandwidth/callback/internal   │   │  /api/bandwidth/callback/internal  │
│       • Handle STOP/START/HELP       │   │       • Handle STOP/START/HELP    │
│         for FL users (update         │   │         for SC users (update      │
│         FL users table)              │   │         SC users table)           │
│       • POST to NC /log-event        │   │       • POST to NC /log-event     │
│         (inbound log)                │   │         (inbound log)              │
└─────────────────────────────────────┘   └───────────────────────────────────┘
```

**Flow summary**

| Step | What happens |
|------|----------------|
| 1 | **Bandwidth** sends all callbacks (delivery, failed, inbound SMS) to **NC** only: `POST /api/bandwidth/callback`. |
| 2 | **NC** parses event type and optional `tag` (set when message was sent: NC, FL, or SC). |
| 3 | **Delivery / failed** – NC updates its own `notification_events` (delivery status). If `tag` is FL or SC, NC forwards that event to that app’s `/api/bandwidth/callback/internal` (FL/SC may ignore or use it; they do not update delivery status). |
| 4 | **Inbound (message-received)** – NC handles STOP/START/HELP for NC users and logs to NC DB. Then NC forwards the **same** event to both FL and SC internal endpoints. |
| 5 | **FL** and **SC** internal endpoints (header `X-Forwarded-By: nc-callback-router`) handle STOP/START/HELP for their own users (update their `users` table). When they log an inbound, they call **NC** `POST /api/bandwidth/log-event` so the event is stored in NC’s `notification_events`. |
| 6 | **Outbound** – When FL or SC send an SMS, they call NC’s `/api/bandwidth/log-event` (with `direction: outbound` and later `message_id`). So when Bandwidth later sends a delivery/failed callback to NC, NC can match by `message_id` and update the same row. |

- **NC**
  - Set `NC_LOG_SECRET` (shared secret for the log-event endpoint).
  - Callback handles delivery status for all states and forwards inbound to FL and SC.

- **FL and SC**
  - Set `NC_LOG_URL` (NC app base URL, e.g. `https://shellcast-web-nc-dot-<project>.appspot.com`).
  - Set `NC_LOG_SECRET` (same value as NC).
  - FL/SC call NC’s `/api/bandwidth/log-event` to record outbound sends and inbound STOP/START.

### SMS cron orchestrator (single cron on NC)

Only the **NC** app has a GAE cron job for SMS. NC runs its own send, then triggers FL and SC by HTTP. FL and SC have no cron entries for SMS; they are invoked by NC.

- **NC**
  - Set `NC_ORCHESTRATOR_SECRET` (shared secret NC sends when calling FL/SC).
  - Cron handler calls FL at `/send_bandwidth_message` and SC at `/send-bandwidth-message` (kebab-case), with header `X-NC-Orchestrator-Secret`.

- **FL**
  - Set `NC_ORCHESTRATOR_SECRET` (same value as NC). The `/send_bandwidth_message` endpoint accepts GAE cron or NC orchestrator (header `X-NC-Orchestrator-Secret`).

- **SC**
  - Set `NC_ORCHESTRATOR_SECRET` (same value as NC). The `/send-bandwidth-message` endpoint accepts GAE cron or NC orchestrator (header `X-NC-Orchestrator-Secret`).

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
