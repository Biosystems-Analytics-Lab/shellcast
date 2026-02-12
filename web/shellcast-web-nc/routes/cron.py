import logging
import os
import secrets
import time

import bandwidth
import requests
from flask import Blueprint, current_app, request
from models import db
from models.NotificationEvent import NotificationEvent
from models.User import User
from routes.authentication import cronOnly
from sqlalchemy import text

# Bandwidth SMS message template
TEXT_NOTIFICATION_MESSAGE = (
    "ShellCast: One or more of your leases is at risk of closing today, tomorrow, or in 2 days. "
    "See https://go.ncsu.edu/shellcast Reply STOP to cancel."
)

# State identifier for NC
STATE = "NC"

cron = Blueprint("cron", __name__)


# =============================================================================
# Bandwidth SMS Notification Functions
# =============================================================================


def get_lease_probabilities_today():
    """
    Call stored procedure using db.session
    """
    result = db.session.execute(text("CALL SelectUserLeaseProbsToday()"))

    # Convert to list of dicts
    column_names = result.keys()
    data = [dict(zip(column_names, row)) for row in result.fetchall()]

    return data


def notification_preprocess_sms():
    """
    Query users who should receive SMS notifications based on their preferences
    and today's closure probabilities.
    Returns list of tuples: (user_id, phone_number)
    """
    # Query users who have opted in for SMS notifications
    users = (
        User.query.filter_by(text_pref=True, text_consent=True, deleted=False)
        .filter(User.phone_number.isnot(None))
        .all()
    )

    users_to_notify = []

    for user in users:
        # Check if any of user's leases have high probability
        for user_lease in user.leases:
            if user_lease.deleted:
                continue
            prob = user_lease.getLatestProbability()
            if prob:
                if (
                    (prob.prob_1d_perc and prob.prob_1d_perc >= user.prob_pref)
                    or (prob.prob_2d_perc and prob.prob_2d_perc >= user.prob_pref)
                    or (prob.prob_3d_perc and prob.prob_3d_perc >= user.prob_pref)
                ):
                    users_to_notify.append((user.id, user.phone_number))
                    break  # Only need to notify once per user

    logging.info(
        f"Found {len(users_to_notify)} users to notify out of {len(users)} eligible users"
    )
    return users_to_notify


def _send_bandwidth_message_single(to_number, message_text=None):
    """
    Send an SMS message to a single recipient using Bandwidth.
    Used for HELP responses.
    """
    if message_text is None:
        message_text = TEXT_NOTIFICATION_MESSAGE

    BW_USERNAME = os.getenv("BW_USERNAME")
    BW_PASSWORD = os.getenv("BW_PASSWORD")
    BW_ACCOUNT_ID = os.getenv("BW_ACCOUNT_ID")
    BW_APPLICATION_ID = os.getenv("BW_APPLICATION_ID")
    BW_FROM_NUMBER = os.getenv("BW_NUMBER")

    configuration = bandwidth.Configuration(username=BW_USERNAME, password=BW_PASSWORD)

    with bandwidth.ApiClient(configuration) as api_client:
        messages_api = bandwidth.MessagesApi(api_client)
        message_request = bandwidth.MessageRequest(
            application_id=BW_APPLICATION_ID,
            to=[to_number],
            var_from=BW_FROM_NUMBER,
            text=message_text,
            tag=STATE,  # Include state for callback routing
        )
        response = messages_api.create_message(BW_ACCOUNT_ID, message_request)
        return response


def _send_bandwidth_message_bulk(users_to_notify):
    """
    Send SMS messages to multiple recipients using Bandwidth.
    users_to_notify: list of tuples (user_id, phone_number)
    """
    if not users_to_notify:
        logging.info("No users to send SMS notifications to")
        return []

    BW_USERNAME = os.getenv("BW_USERNAME")
    BW_PASSWORD = os.getenv("BW_PASSWORD")
    BW_ACCOUNT_ID = os.getenv("BW_ACCOUNT_ID")
    BW_APPLICATION_ID = os.getenv("BW_APPLICATION_ID")
    BW_FROM_NUMBER = os.getenv("BW_NUMBER")

    configuration = bandwidth.Configuration(username=BW_USERNAME, password=BW_PASSWORD)
    results = []

    with bandwidth.ApiClient(configuration) as api_client:
        messages_api = bandwidth.MessagesApi(api_client)

        for user_id, phone_number in users_to_notify:
            try:
                message_request = bandwidth.MessageRequest(
                    application_id=BW_APPLICATION_ID,
                    to=[phone_number],
                    var_from=BW_FROM_NUMBER,
                    text=TEXT_NOTIFICATION_MESSAGE,
                    tag=STATE,  # Include state for callback routing
                )
                response = messages_api.create_message(BW_ACCOUNT_ID, message_request)

                # Log the notification event
                event = NotificationEvent.log_sms_outbound(
                    state=STATE,
                    user_id=user_id,
                    phone_number=phone_number,
                    template_name=NotificationEvent.TEMPLATE_SMS_CLOSURE_ALERT,
                    message_id=response.id if response else None,
                    send_success=True,
                )
                db.session.add(event)
                results.append(
                    (user_id, phone_number, True, response.id if response else None)
                )
                logging.info(f"SMS sent to {phone_number} for user {user_id}")

            except Exception as e:
                logging.error(f"Failed to send SMS to {phone_number}: {e}")
                # Log failed attempt
                event = NotificationEvent.log_sms_outbound(
                    state=STATE,
                    user_id=user_id,
                    phone_number=phone_number,
                    template_name=NotificationEvent.TEMPLATE_SMS_CLOSURE_ALERT,
                    message_id=None,
                    send_success=False,
                )
                db.session.add(event)
                results.append((user_id, phone_number, False, None))

            # Small delay to avoid rate limiting
            time.sleep(0.1)

        db.session.commit()

    return results


def _trigger_state_send(state):
    """
    Trigger the state app's /send_bandwidth_message (used when cron runs only on NC).
    POSTs with X-NC-Orchestrator-Secret so FL/SC accept the request.
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "ncsu-shellcast")
    secret = os.getenv("NC_ORCHESTRATOR_SECRET")
    if not secret:
        logging.warning("NC_ORCHESTRATOR_SECRET not set; cannot trigger %s send", state)
        return None
    url = f"https://shellcast-{state.lower()}-dot-{project_id}.appspot.com/send_bandwidth_message"
    try:
        r = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "X-NC-Orchestrator-Secret": secret,
            },
            timeout=120,
        )
        logging.info("Triggered %s send_bandwidth_message: %s", state, r.status_code)
        return r.status_code
    except Exception as e:
        logging.error("Failed to trigger %s send: %s", state, e)
        return None


@cron.route("/send_bandwidth_message", methods=["POST"])
@cronOnly
def send_bandwidth_message():
    """
    Cron endpoint: run NC SMS send, then trigger FL and SC sends.
    GAE cron hits only NC; NC orchestrates FL and SC via HTTP.
    """
    logging.info("Starting Bandwidth SMS notification send (NC + FL + SC)...")
    t0 = time.perf_counter_ns()

    # 1. NC own send
    users_to_notify = notification_preprocess_sms()
    results = _send_bandwidth_message_bulk(users_to_notify)
    nc_success = sum(1 for r in results if r[2])
    nc_fail = len(results) - nc_success

    # 2. Trigger FL and SC (they run their own send + log to NC)
    fl_status = _trigger_state_send("FL")
    sc_status = _trigger_state_send("SC")

    t1 = time.perf_counter_ns()
    parts = [
        f"NC: {nc_success} sent ({nc_fail} failed)",
        f"FL: {fl_status or 'skip'}",
        f"SC: {sc_status or 'skip'}",
        f"in {(t1 - t0) / 1e9:.2f}s",
    ]
    result = "; ".join(parts)
    logging.info(result)

    return result, 200


# Bandwidth callback is handled in api.py via /api/bandwidth/callback
# NC receives all callbacks and routes SC/FL callbacks to their respective services


# =============================================================================
# Test endpoint (for local development only)
# =============================================================================


@cron.route("/test/send_sms", methods=["POST", "GET"])
def test_send_sms():
    """
    Test endpoint for sending SMS - DO NOT USE IN PRODUCTION.
    Only works when DEBUG mode is enabled.
    """
    if not current_app.config.get("DEBUG"):
        return "Not allowed in production", 403

    test_number = request.args.get("phone")
    if not test_number:
        return "Missing 'phone' parameter", 400

    try:
        response = _send_bandwidth_message_single(test_number)
        return f"SMS sent! Message ID: {response.id if response else 'unknown'}", 200
    except Exception as e:
        return f"Failed to send SMS: {e}", 500


# =============================================================================
# Production smoke test (one-off SMS to a consented user from DB)
# =============================================================================

SMOKE_TEST_MESSAGE = "ShellCast smoke test – if you received this, SMS is working."


def _phone_to_e164(phone):
    """Format phone for Bandwidth (E.164). Assume US: 10 digits -> +1xxxxxxxxxx."""
    if not phone:
        return None
    digits = "".join(c for c in str(phone) if c.isdigit())
    if len(digits) == 10:
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    return phone if phone.startswith("+") else "+" + digits


@cron.route("/cron/smoke-test-sms", methods=["GET", "POST"])
def smoke_test_sms():
    """
    One-off smoke test: send a single SMS to the phone of the given user (from DB).
    Requires user_id (query or JSON). Secured by SMOKE_TEXT_SECRET (?token= or header).
    The developer must have consented to text notifications and set their phone
    in Preferences before testing; otherwise the endpoint returns 400.
    Example: GET .../cron/smoke-test-sms?token=YOUR_SECRET&user_id=123
    """
    secret = os.getenv("SMOKE_TEXT_SECRET")
    if not secret:
        logging.warning("smoke_test_sms: SMOKE_TEXT_SECRET not set")
        return {"ok": False, "error": "Smoke test not configured"}, 503

    token = request.args.get("token") or request.headers.get("X-Smoke-Test-Token")
    if not token or not secrets.compare_digest(token, secret):
        logging.warning("smoke_test_sms: invalid or missing token")
        return {"ok": False, "error": "Forbidden"}, 403

    user_id = request.args.get("user_id")
    if request.is_json:
        user_id = user_id or (request.get_json(silent=True) or {}).get("user_id")
    if not user_id:
        return {"ok": False, "error": "user_id required (query or JSON)"}, 400
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return {"ok": False, "error": "user_id must be an integer"}, 400

    user = User.query.get(user_id)
    if not user:
        return {"ok": False, "error": "User not found"}, 404
    if not user.phone_number or not user.phone_number.strip():
        return {
            "ok": False,
            "error": "User has no phone number. Set phone in Preferences first.",
        }, 400
    if not user.text_pref or not user.text_consent:
        return {
            "ok": False,
            "error": "User has not consented to text notifications. Enable text in Preferences and consent first.",
        }, 400

    phone_e164 = _phone_to_e164(user.phone_number)
    digits = "".join(c for c in user.phone_number if c.isdigit())
    clean_phone = (
        digits[-10:] if len(digits) >= 10 else digits
    )  # 10-digit for DB consistency

    try:
        response = _send_bandwidth_message_single(
            phone_e164 or user.phone_number, message_text=SMOKE_TEST_MESSAGE
        )
        msg_id = response.id if response else None
        logging.info(
            "smoke_test_sms: SMS sent to user_id=%s phone=%s message_id=%s",
            user.id,
            phone_e164,
            msg_id,
        )

        event = NotificationEvent.log_sms_outbound(
            state=STATE,
            user_id=user.id,
            phone_number=clean_phone,
            template_name=NotificationEvent.TEMPLATE_SMS_SMOKE_TEST,
            message_id=msg_id,
            send_success=True,
        )
        db.session.add(event)
        db.session.commit()

        return {"ok": True, "message": "SMS sent", "message_id": msg_id}, 200
    except Exception as e:
        logging.exception("smoke_test_sms: failed to send SMS")
        return {"ok": False, "error": str(e)}, 500
