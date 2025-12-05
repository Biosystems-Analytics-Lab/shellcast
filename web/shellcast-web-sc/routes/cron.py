import logging
import os
import time
from datetime import datetime, timezone

import bandwidth
import boto3
import pytz
from bandwidth.bandwidth_client import BandwidthClient
from bandwidth.rest import ApiException
from botocore.exceptions import ClientError
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

cron = Blueprint("cron", __name__)


bandwidth_client = BandwidthClient(
    messaging_basic_auth_user_name=current_app.config["BW_USERNAME"],
    messaging_basic_auth_password=current_app.config["BW_PASSWORD"],
)
messaging_client = bandwidth_client.messaging_client.client

# from bandwidth.messaging.models.message_request import MessageRequest

# messagingBody = MessageRequest()
# messagingBody.to = ["{to}"]
# messagingBody.mfrom = "{from}"
# messagingBody.text = "Hello, I am sending a message! How fun!"
# messagingBody.application_id = "{app_id}"

# messaging_client.create_message("{account_id}", body=messagingBody)

# @app.route("/messaging", methods=["POST"])
# def messaging():
#     data = json.loads(request.data)
#     if (data[0].get("type") == "message-delivered"):
#         //successful delivery action
#         return ('', 200)
#     if (data[0].get("type") == "message-failed"):
#         failure_reason = data[0].get("description");
#         //failed delivery action
#         return ('', 200)
#     return ('', 200)
# app.run()

# def sendEmailWithAWSSES(client, address, subject, body):
# try:
#     response = client.send_email(
#         Destination={"ToAddresses": [address]},
#         Message={
#             "Subject": {"Charset": CHARSET, "Data": subject},
#             "Body": {"Text": {"Charset": CHARSET, "Data": body}},
#         },
#         Source=SENDER,
#     )
# except ClientError as e:
#     logging.error("Error while sending email to " + address)
#     logging.error(e.response["Error"]["Message"])
#     return False, e.response["Error"]["Message"]
# else:
#     logging.info("Email successfully sent to " + address)
#     logging.info(response["MessageId"])
#     return True, response["MessageId"]


# def sendNotificationsWithAWSSES(emailNotifications, textNotifications):
# Create a new SES client
# client = boto3.client(
#     "ses",
#     region_name=current_app.config["AWS_REGION"],
#     aws_access_key_id=current_app.config["AWS_ACCESS_KEY_ID"],
#     aws_secret_access_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
# )
# curDate = datetime.now(pytz.timezone("US/Eastern")).strftime("%m/%d/%Y")
# emailNotificationSubject = SUBJECT_TEMPLATE.format(curDate)
# responses = []
# # send the email notifications
# for address, emailBodyChunks, userId in emailNotifications:
#     body = "".join(emailBodyChunks)
#     sendSuccess, response = sendEmailWithAWSSES(
#         client, address, emailNotificationSubject, body
#     )
#     responses.append(
#         (address, body, NOTIFICATION_TYPE_EMAIL, userId, sendSuccess, response)
#     )
#     time.sleep(
#         EMAIL_SEND_INTERVAL
#     )  # add a delay so that we don't exceed our max send rate (currently 14 emails/second)
# # send the text notifications
# for address, body, userId in textNotifications:
#     sendSuccess, response = sendEmailWithAWSSES(
#         client, address, TEXT_NOTIFICATION_SUBJECT, body
#     )
#     responses.append(
#         (address, body, NOTIFICATION_TYPE_TEXT, userId, sendSuccess, response)
#     )
#     time.sleep(
#         EMAIL_SEND_INTERVAL
#     )  # add a delay so that we don't exceed our max send rate (currently 14 emails/second)
# return responses


# def probabilityToRisk(closureValue):
#     flag = ""
#     if closureValue == 1:
#         flag = "Very Low"
#     elif closureValue == 2:
#         flag = "Low"
#     elif closureValue == 3:
#         flag = "Moderate"
#     elif closureValue == 4:
#         flag = "High"
#     elif closureValue == 5:
#         flag = "Very High"
#     return flag


def notification_preprocess():
    phone_numbers_to_send = []
    # Get probability data
    data = execute_stored_procedure(
        current_app.config["SQLALCHEMY_DATABASE_URI"], "SelectUserLeaseProbsToday"
    )
    # Process probability data
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
                # data_to_send = {"from": current_app.config["BW_NUMBER"], "to": row["phone_number"], "body": TEXT_NOTIFICATION_TEXT}
                phone_numbers_to_send.append(row["phone_number"])

    return phone_numbers_to_send


@cron.route("/send_bandwidth_message", methods=["POST"])
@cronOnly
def send_bandwidth_message():
    """
    Send an SMS message using Bandwidth.
    """
    phone_numbers_to_send = notification_preprocess()
    _send_bandwidth_message(phone_numbers_to_send)
    return "", 200


def _send_bandwidth_message(to_numbers):
    """
    Send an SMS message using Bandwidth.
    """
    BW_USERNAME = os.getenv("BW_USERNAME")
    BW_PASSWORD = os.getenv("BW_PASSWORD")
    BW_ACCOUNT_ID = os.getenv("BW_ACCOUNT_ID")
    BW_APPLICATION_ID = os.getenv("BW_APPLICATION_ID")
    BW_FROM_NUMBER = os.getenv("BW_NUMBER")

    # Configure Bandwidth client
    configuration = bandwidth.Configuration(username=BW_USERNAME, password=BW_PASSWORD)

    # Use context manager
    with bandwidth.ApiClient(configuration) as api_client:
        # Create MessagesApi instance
        messages_api = bandwidth.MessagesApi(api_client)

        # Create MessageRequest
        message_request = bandwidth.MessageRequest(
            application_id=BW_APPLICATION_ID,
            to=to_numbers,
            var_from=BW_FROM_NUMBER,
            text=TEXT_NOTIFICATION_MESSAGE,
        )
        response = messages_api.create_message(BW_ACCOUNT_ID, message_request)
        return response


@cron.route("/bandwidth/callback", methods=["POST"])
def bandwidthCallback():
    """
    Handle callbacks from Bandwidth for SMS delivery status and incoming messages.
    This endpoint receives webhooks for:
    - message-delivered: SMS was successfully delivered
    - message-failed: SMS delivery failed
    - message-received: Incoming SMS from user (e.g., STOP/START commands)
    """
    try:
        # Bandwidth sends an array of message events
        callback_data = request.json

        if not callback_data:
            logging.warning("Received empty callback from Bandwidth")
            return "", 200

        # Process each event in the callback
        for event in callback_data:
            event_type = event.get("type")
            message_id = event.get("message", {}).get("id")
            to_number = event.get("message", {}).get("to", [None])[0]
            from_number = event.get("message", {}).get("from")
            text = event.get("message", {}).get("text", "")

            logging.info(
                f"Bandwidth callback received - Type: {event_type}, Message ID: {message_id}"
            )

            if event_type == "message-delivered":
                # SMS was successfully delivered
                logging.info(
                    f"Message {message_id} delivered successfully to {to_number}"
                )

            elif event_type == "message-failed":
                # SMS delivery failed
                error_code = event.get("errorCode")
                description = event.get("description")
                logging.error(
                    f"Message {message_id} failed to {to_number}: {description} (Code: {error_code})"
                )

            elif event_type == "message-received":
                # Incoming SMS from user (e.g., STOP, START, HELP)
                logging.info(f"Received SMS from {from_number}: {text}")

                # Handle opt-out keywords (STOP, UNSUBSCRIBE, CANCEL, END, QUIT)
                text_upper = text.strip().upper()
                if text_upper in ["STOP", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"]:
                    # Find user by phone number and disable text notifications
                    user = (
                        db.session.query(User)
                        .filter_by(phone_number=from_number)
                        .first()
                    )
                    if user:
                        user.text_pref = False
                        user.text_opt_out_date = datetime.now(timezone.utc)
                        db.session.add(user)
                        db.session.commit()
                        logging.info(f"User {user.id} opted out of SMS notifications")

                elif text_upper in ["HELP"]:
                    # Send help message
                    logging.info(f"Sending help message to {from_number}")
                    _send_bandwidth_message(from_number, HELP_MESSAGE)
                    logging.info(f"Help message sent")

                # Handle opt-in keywords (START, UNSTOP)
                # elif text_upper in ["START", "UNSTOP"]:
                #     # Find user by phone number and enable text notifications
                #     user = db.session.query(User).filter_by(phone_number=from_number).first()
                #     if user:
                #         user.text_consent = True
                #         db.session.add(user)
                #         db.session.commit()
                #         logging.info(f"User {user.id} opted back in to SMS notifications")

            else:
                logging.warning(f"Unknown event type received: {event_type}")

        # Always return 200 OK to acknowledge receipt
        return "", 200

    except Exception as e:
        logging.error(f"Error processing Bandwidth callback: {e}")
        # Still return 200 to prevent Bandwidth from retrying
        return "", 200


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
