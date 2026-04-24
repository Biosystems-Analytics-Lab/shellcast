import logging
import os
import secrets
import time

from core.notifications.bandwidth_send import send_sms_batch, send_sms_single
from flask import Blueprint, current_app, request
from models import db
from models.User import User
from routes.authentication import cron_only

# State identifier for FL
STATE = "FL"
# Bandwidth SMS message template (FL only has 1-day forecast)
TEXT_NOTIFICATION_MESSAGE = (
    f"ShellCast-{STATE}: One or more of your leases is at risk of closing today. "
    "See https://go.ncsu.edu/shellcast Reply STOP to cancel."
)

cron = Blueprint("cron", __name__)


# =============================================================================
# Bandwidth SMS Notification Functions
# =============================================================================


def _get_sms_opted_in_users():
    """Return users who are SMS-opted-in, verified, and have a phone number."""
    return (
        db.session.query(User)
        .filter_by(
            deleted=False,
            text_pref=True,
            text_consent=True,
            phone_verified=True,
        )
        .filter(User.phone_number.isnot(None))
        .all()
    )


def notification_preprocess_sms():
    """
    Query users who should receive SMS notifications based on their preferences
    and today's closure probabilities.
    Returns list of tuples: (user_id, phone_number)
    """
    users_to_notify = []
    users = _get_sms_opted_in_users()

    for user in users:
        # Check if any of user's leases have high probability
        for user_lease in user.leases:
            if user_lease.deleted:
                continue
            prob = user_lease.getLatestProbability()
            if prob:
                # FL only has 1-day probability
                if prob.prob_1d_perc and prob.prob_1d_perc >= user.prob_pref:
                    users_to_notify.append((user.id, user.phone_number))
                    break  # Only need to notify once per user

    return users_to_notify


def notification_preprocess_sms_for_test():
    """
    Same as notification_preprocess_sms but ignores closure probability.
    Returns all opted-in users with a phone number (for testing notifications).
    """
    users = _get_sms_opted_in_users()
    return [(u.id, u.phone_number) for u in users]


def _send_bandwidth_message_single(to_number, message_text=None):
    """Send one SMS via Bandwidth (STOP/START/HELP replies). Delegates to core."""
    text = message_text if message_text is not None else TEXT_NOTIFICATION_MESSAGE
    return send_sms_single(to_number, text, STATE)


def _send_bandwidth_message_bulk(users_to_notify):
    """Send SMS messages to multiple recipients using Bandwidth.

    users_to_notify: list of tuples (user_id, phone_number)
    Returns list of (user_id, phone_number, success, message_id).
    """
    if not users_to_notify:
        logging.info(f"No users to send {STATE} SMS notifications to")
        return []

    return send_sms_batch(
        users_to_notify,
        text=TEXT_NOTIFICATION_MESSAGE,
        state=STATE,
        sleep_seconds=0.1,
    )


@cron.route("/cron/test-notifications", methods=["GET", "POST"])
def test_notifications():
    """
    Send SMS to all opted-in users regardless of closure probability (for testing).
    Secured by SMOKE_TEXT_SECRET (?token= or X-Smoke-Test-Token header).
    """
    from routes.api import TEMPLATE_SMS_CLOSURE_ALERT, _log_sms_to_nc

    secret = os.getenv("SMOKE_TEXT_SECRET")
    if not secret:
        logging.warning("test_notifications: SMOKE_TEXT_SECRET not set")
        return {"ok": False, "error": "Test not configured"}, 503

    token = request.args.get("token") or request.headers.get("X-Smoke-Test-Token")
    if not token or not secrets.compare_digest(token, secret):
        logging.warning("test_notifications: invalid or missing token")
        return {"ok": False, "error": "Forbidden"}, 403

    logging.info("Test notifications (ignore probability) - FL...")
    users_to_notify = notification_preprocess_sms_for_test()
    results = _send_bandwidth_message_bulk(users_to_notify)
    for user_id, phone_number, success, message_id in results:
        if success and message_id:
            _log_sms_to_nc(
                state=STATE,
                user_id=user_id,
                phone_number=phone_number,
                direction="outbound",
                message_id=message_id,
                template_name=TEMPLATE_SMS_CLOSURE_ALERT,
                send_success=True,
            )
    success_count = sum(1 for r in results if r[2])
    fail_count = len(results) - success_count
    return {
        "ok": True,
        "state": STATE,
        "sent": success_count,
        "failed": fail_count,
        "total": len(results),
        "message": f"Test: sent {success_count} SMS to opted-in users (no probability check).",
    }, 200


@cron.route("/send-bandwidth-message", methods=["POST"])
@cron_only
def send_bandwidth_message():
    """
    Cron endpoint to send SMS notifications using Bandwidth.
    Logs each outbound to NC's notification_events.
    """
    from routes.api import TEMPLATE_SMS_CLOSURE_ALERT, _log_sms_to_nc

    logging.info("Starting Bandwidth SMS notification send for FL...")
    t0 = time.perf_counter_ns()

    users_to_notify = notification_preprocess_sms()
    results = _send_bandwidth_message_bulk(users_to_notify)

    for user_id, phone_number, success, message_id in results:
        if success and message_id:
            _log_sms_to_nc(
                state=STATE,
                user_id=user_id,
                phone_number=phone_number,
                direction="outbound",
                message_id=message_id,
                template_name=TEMPLATE_SMS_CLOSURE_ALERT,
                send_success=True,
            )

    success_count = sum(1 for r in results if r[2])
    fail_count = len(results) - success_count

    t1 = time.perf_counter_ns()
    result = f"FL: Sent {success_count} SMS notifications ({fail_count} failed) in {(t1 - t0) / 1e9:.2f} seconds"
    logging.info(result)

    return result, 200


# Bandwidth callback (from NC) is handled in api.py via /api/bandwidth/callback/internal
# NC service receives all callbacks and routes FL callbacks to this service


# =============================================================================
# Test endpoint (for local development only)
# =============================================================================


@cron.route("/test/send-sms", methods=["POST", "GET"])
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
