import logging
import os
import time

import bandwidth
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
                    template_name="sms_closure_alert",
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
                    template_name="sms_closure_alert",
                    message_id=None,
                    send_success=False,
                )
                db.session.add(event)
                results.append((user_id, phone_number, False, None))

            # Small delay to avoid rate limiting
            time.sleep(0.1)

        db.session.commit()

    return results


@cron.route("/send_bandwidth_message", methods=["POST"])
@cronOnly
def send_bandwidth_message():
    """
    Cron endpoint to send SMS notifications using Bandwidth.
    """
    logging.info("Starting Bandwidth SMS notification send...")
    t0 = time.perf_counter_ns()

    users_to_notify = notification_preprocess_sms()
    results = _send_bandwidth_message_bulk(users_to_notify)

    success_count = sum(1 for r in results if r[2])
    fail_count = len(results) - success_count

    t1 = time.perf_counter_ns()
    result = f"Sent {success_count} SMS notifications ({fail_count} failed) in {(t1 - t0) / 1e9:.2f} seconds"
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
