import logging
import os
from datetime import datetime, timezone

from botocore.exceptions import ClientError
from core.notifications.bandwidth_send import send_sms_batch, send_sms_single
from flask import Blueprint, current_app, request
from models import db
from models.Notification import Notification
from models.User import User
from routes.authentication import cronOnly
from utils import execute_stored_procedure

# The address that all emails are sent from.
# This address must be verified with Amazon SES.
SENDER = "ShellCast <shellcastapp@ncsu.edu>"
# The subject line template for all emails.
SUBJECT_TEMPLATE = "SC ShellCast Forecasts for {}"
# The character encoding for all emails.
CHARSET = "UTF-8"
# The text that is at the beginning of every notification.
NOTIFICATION_HEADER = "https://go.ncsu.edu/shellcast\n\n"
# The template for lease information in notifications.
LEASE_TEMPLATE = "One or more of your leases is at risk of closing today, tomorrow or in 2 days.\nVisit go.ncsu.edu/shellcast for details.\n\nLease: {}\n  Today: {}\n  Tomorrow: {}\n  In 2 days: {}\n"
# The text that is at the end of every notification.
NOTIFICATION_FOOTER = "\nThese predictions are in no way indicative of whether or not a lease will actually be temporarily closed for harvest."
# The amount of time between sending emails
EMAIL_SEND_INTERVAL = 0.1
# The subject for text notifications
TEXT_NOTIFICATION_SUBJECT = ""
# The text for text notifications (max length of 138 characters)
TEXT_NOTIFICATION_MESSAGE = "ShellCast: One or more of your leases is at risk of closing today, tomorrow, or in 2 days. See https://go.ncsu.edu/shellcast Reply STOP to cancel."
HELP_MESSAGE = "Thank you for reaching out to ShellCast. For support, please email us at shellcastapp@ncsu.edu. Reply STOP to opt out."

NOTIFICATION_TYPE_EMAIL = "email"
NOTIFICATION_TYPE_TEXT = "text"

# State identifier for callback routing and NC logging
STATE = "SC"

cron = Blueprint("cron", __name__)


def notification_preprocess():
    """
    Return list of (user_id, phone_number) for users who should receive SMS.
    """
    users_to_send = []
    data = execute_stored_procedure(
        current_app.config["SQLALCHEMY_DATABASE_URI"], "SelectUserLeaseProbsToday"
    )
    for row in data:
        if (
            (row["text_pref"] and row["text_consent"])
            and row["phone_number"] is not None
            and row["prob_pref"] is not None
        ):
            if (
                row["prob_pref"] <= row["prob_1d_perc"]
                or row["prob_pref"] <= row["prob_2d_perc"]
                or row["prob_pref"] <= row["prob_3d_perc"]
            ):
                users_to_send.append((row["user_id"], row["phone_number"]))

    return users_to_send


@cron.route("/send_bandwidth_message", methods=["POST"])
@cronOnly
def send_bandwidth_message():
    """
    Send SMS notifications per user using Bandwidth. Logs each to NC notification_events.
    """
    from routes.api import TEMPLATE_SMS_CLOSURE_ALERT, _log_sms_to_nc

    users_to_notify = notification_preprocess()
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

    return "", 200


def _send_bandwidth_message_single(to_number, message_text=None):
    """Send one SMS via Bandwidth (STOP/START/HELP replies). Delegates to core."""
    text = message_text if message_text is not None else TEXT_NOTIFICATION_MESSAGE
    return send_sms_single(to_number, text, STATE)


def _send_bandwidth_message_bulk(users_to_notify):
    """Send SMS to multiple users.

    users_to_notify: list of (user_id, phone_number).
    Returns list of (user_id, phone_number, success, message_id).
    """
    if not users_to_notify:
        logging.info(f"No users to send {STATE} SMS notifications to")
        return []

    return send_sms_batch(
        users_to_notify,
        text=TEXT_NOTIFICATION_MESSAGE,
        state=STATE,
        sleep_seconds=0.0,
    )


# Bandwidth callback is handled in api.py via /api/bandwidth/callback/internal
# NC service receives all callbacks and routes SC callbacks to this service


# @cron.route("/sendNotifications")
# @cronOnly
# def sendNotifications():
#     """
#     Sends notifications to all users whose leases warrant a notification.
#     """
#     logging.info("Constructing and sending notifications...")
#     t0 = time.perf_counter_ns()
#     emailNotificationsToSend = []
#     textNotificationsToSend = []
#     # build the notifications for each user
#     users = db.session.query(User).filter_by(deleted=False).all()
#     for user in users:
#         # get email address
#         emailAddress = user.email
#         # get phone number and service provider gateway (phonenumber@smsgateway)
#         textAddress = None
#         if user.phone_number is not None and user.service_provider_id is not None:
#             textAddress = "{}@{}".format(
#                 user.phone_number, user.service_provider.sms_gateway
#             )
#         # construct notification text
#         notificationText = [NOTIFICATION_HEADER]
#         needToSendNotification = False
#         # for each of the user's leases
#         for lease in user.leases:
#             # get the latest closure probability for the lease
#             prob = lease.getLatestProbability()
#             # if the lease has not been deleted and there's a probability for the lease
#             if not lease.deleted and prob:
#                 # if any of the day probs are >= the user's prob preference
#                 if (
#                     (prob.prob_1d_perc and prob.prob_1d_perc >= user.prob_pref)
#                     or (prob.prob_2d_perc and prob.prob_2d_perc >= user.prob_pref)
#                     or (prob.prob_3d_perc and prob.prob_3d_perc >= user.prob_pref)
#                 ):
#                     leaseInfo = LEASE_TEMPLATE.format(
#                         lease.lease_id,
#                         probabilityToRisk(prob.prob_1d_perc),
#                         probabilityToRisk(prob.prob_2d_perc),
#                         probabilityToRisk(prob.prob_3d_perc),
#                     )
#                     notificationText.append(leaseInfo)
#                     needToSendNotification = True
#         # add a disclaimer to the end of the notifications
#         notificationText.append(NOTIFICATION_FOOTER)

#         if needToSendNotification:
#             # only send emails or texts depending on the user's preferences
#             if user.email_pref and emailAddress is not None:
#                 emailNotificationsToSend.append(
#                     (emailAddress, notificationText, user.id)
#                 )
#             if user.text_pref and textAddress is not None:
#                 textNotificationsToSend.append(
#                     (textAddress, TEXT_NOTIFICATION_TEXT, user.id)
#                 )

#     # send notifications
#     responses = sendNotificationsWithAWSSES(
#         emailNotificationsToSend, textNotificationsToSend
#     )
#     # log all notifications that were sent
#     for (
#         address,
#         notificationText,
#         notificationType,
#         userId,
#         sendSuccess,
#         resText,
#     ) in responses:
#         notification = Notification(
#             address=address,
#             notification_text=notificationText,
#             notification_type=notificationType,
#             user_id=userId,
#             send_success=sendSuccess,
#             response_text=resText,
#         )
#         db.session.add(notification)
#     db.session.commit()
#     t1 = time.perf_counter_ns()
#     result = "Constructed and sent {} email notifications and {} text notifications to {} users in {} seconds".format(
#         len(emailNotificationsToSend),
#         len(textNotificationsToSend),
#         len(users),
#         (t1 - t0) / 1000000000,
#     )
#     logging.info(result)
#     return result
