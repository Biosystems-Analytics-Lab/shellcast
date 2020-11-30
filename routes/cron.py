import logging
import time
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timezone
import pytz
import boto3
from botocore.exceptions import ClientError

from models import db
from models.User import User
from models.Notification import Notification

from routes.authentication import cronOnly

# The address that all emails are sent from.
# This address must be verified with Amazon SES.
SENDER = 'ShellCast <shellcastapp@ncsu.edu>'
# The subject line template for all emails.
SUBJECT_TEMPLATE = 'ShellCast Predictions: % Chance of Lease Closure for {}'
# The character encoding for all emails.
CHARSET = 'UTF-8'
# The text that is at the beginning of every notification.
NOTIFICATION_HEADER = 'https://go.ncsu.edu/shellcast\n\n'
# The template for lease information in notifications.
LEASE_TEMPLATE =  'Lease: {}\n  1-day: {}%\n  2-day: {}%\n  3-day: {}%\n'
# The text that is at the end of every notification.
NOTIFICATION_FOOTER = '\nThese predictions are in no way indicative of whether or not a growing area will actually be temporarily closed for harvest.'
# The amount of time between sending emails
EMAIL_SEND_INTERVAL = 0.1
# The maximum size of SMS messages
MAX_SMS_MESSAGE_SIZE = 120

cron = Blueprint('cron', __name__)

def sendEmailWithAWSSES(client, address, subject, body):
  try:
    response = client.send_email(
      Destination={'ToAddresses': [address]},
      Message={
        'Subject': {'Charset': CHARSET, 'Data': subject},
        'Body': {'Text': {'Charset': CHARSET, 'Data': body}}
      },
      Source=SENDER,
    )
  except ClientError as e:
    logging.error('Error while sending email to ' + address)
    logging.error(e.response['Error']['Message'])
    return False, e.response['Error']['Message']
  else:
    logging.info('Email successfully sent to ' + address)
    logging.info(response['MessageId'])
    return True, response['MessageId']

def groupTextBodyChunks(textBodyChunks):
  notificationParts = []

  notificationPart = ''
  # go through each body chunk
  for textBodyChunk in textBodyChunks:
    # if the body chunk can fit in the current part
    if (len(notificationPart) + len(textBodyChunk) <= MAX_SMS_MESSAGE_SIZE):
      notificationPart += textBodyChunk # add it
    else: # else it can't fit
      notificationParts.append(notificationPart) # so finalize the current part
      notificationPart = textBodyChunk # start the new part

  # add the last notification part
  notificationParts.append(notificationPart)

  return notificationParts


def sendNotificationsWithAWSSES(emailNotifications, textNotifications):
  # Create a new SES client
  client = boto3.client('ses', region_name=current_app.config['AWS_REGION'], aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'], aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'])
  curDate = datetime.now(pytz.timezone('US/Eastern')).strftime('%m/%d/%Y')
  subject = SUBJECT_TEMPLATE.format(curDate)
  responses = []
  # send the email notifications
  for address, emailBodyChunks, userId in emailNotifications:
    body = ''.join(emailBodyChunks)
    sendSuccess, response = sendEmailWithAWSSES(client, address, subject, body)
    responses.append((address, body, userId, sendSuccess, response))
    time.sleep(EMAIL_SEND_INTERVAL) # add a delay so that we don't exceed our max send rate (currently 14 emails/second)
  # send the text notifications
  for address, textBodyChunks, userId in textNotifications:
    # split the notification up into parts so that it can be sent through SMS (SMS has a limit on the size of messages)
    notificationParts = groupTextBodyChunks(textBodyChunks)
    overallSendSuccess = True
    partResponses = []
    for partIdx in range(len(notificationParts)):
      # send the original subject for the first part; send part indices for the remaining parts
      partSubject = subject if partIdx == 0 else f'{partIdx + 1}/{len(notificationParts)}' # e.g. 2/3
      partBody = notificationParts[partIdx]
      sendSuccess, response = sendEmailWithAWSSES(client, address, partSubject, partBody)
      if not sendSuccess:
        overallSendSuccess = False
      partResponses.append(response)
      time.sleep(EMAIL_SEND_INTERVAL) # add a delay so that we don't exceed our max send rate (currently 14 emails/second)

    fullBody = ''.join(textBodyChunks)
    responses.append((address, fullBody, userId, overallSendSuccess, ','.join(partResponses)))
  return responses

@cron.route('/sendNotifications')
@cronOnly
def sendNotifications():
  """
  Sends notifications to all users whose leases warrant a notification.
  """
  logging.info('Constructing and sending notifications...')
  t0 = time.perf_counter_ns()
  emailNotificationsToSend = []
  textNotificationsToSend = []
  # build the notifications for each user
  users = db.session.query(User).all()
  for user in users:
    # get email address
    emailAddress = user.email
    # get phone number and service provider gateway (phonenumber@smsgateway)
    textAddress = None
    if (user.phone_number != None and user.service_provider_id != None):
      textAddress = '{}@{}'.format(user.phone_number, user.service_provider.sms_gateway)
    # construct notification text
    notificationText = [NOTIFICATION_HEADER]
    needToSendNotification = False
    # for each of the user's leases
    for lease in user.leases:
      # get the latest closure probability for the lease
      prob = lease.getLatestProbability()
      # if the lease has not been deleted and there's a probability for the lease
      if (not lease.deleted and prob):
        # if any of the day probs are >= the user's prob preference
        if ((prob.prob_1d_perc and prob.prob_1d_perc >= user.prob_pref) or
            (prob.prob_2d_perc and prob.prob_2d_perc >= user.prob_pref) or
            (prob.prob_3d_perc and prob.prob_3d_perc >= user.prob_pref)):
          leaseInfo = LEASE_TEMPLATE.format(lease.ncdmf_lease_id, prob.prob_1d_perc, prob.prob_2d_perc, prob.prob_3d_perc)
          notificationText.append(leaseInfo)
          needToSendNotification = True
    # add a disclaimer to the end of the notifications
    notificationText.append(NOTIFICATION_FOOTER)

    if (needToSendNotification):
      # only send emails or texts depending on the user's preferences
      if (user.email_pref and emailAddress != None):
        emailNotificationsToSend.append((emailAddress, notificationText, user.id))
      if (user.text_pref and textAddress != None):
        textNotificationsToSend.append((textAddress, notificationText, user.id))

  # send notifications
  responses = sendNotificationsWithAWSSES(emailNotificationsToSend, textNotificationsToSend)
  # log all notifications that were sent
  for address, notificationText, userId, sendSuccess, resText in responses:
    notification = Notification(address=address, notification_text=notificationText, user_id=userId, send_success=sendSuccess, response_text=resText)
    db.session.add(notification)
  db.session.commit()
  t1 = time.perf_counter_ns()
  result = 'Constructed and sent {} email notifications and {} text notifications to {} users in {} seconds'.format(len(emailNotificationsToSend), len(textNotificationsToSend), len(users), (t1 - t0) / 1000000000)
  logging.info(result)
  return result
