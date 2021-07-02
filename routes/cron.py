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
SUBJECT_TEMPLATE = 'ShellCast Forecasts for {}'
# The character encoding for all emails.
CHARSET = 'UTF-8'
# The text that is at the beginning of every notification.
NOTIFICATION_HEADER = 'https://go.ncsu.edu/shellcast\n\n'
# The template for lease information in notifications.
LEASE_TEMPLATE =  'One or more of your leases is at risk of closing today, tomorrow or in 2 days.\nVisit go.ncsu.edu/shellcast for details.\n\nLease: {}\n  Today: {}\n  Tomorrow: {}\n  In 2 days: {}\n'
# The text that is at the end of every notification.
NOTIFICATION_FOOTER = '\nThese predictions are in no way indicative of whether or not a lease will actually be temporarily closed for harvest.'
# The amount of time between sending emails
EMAIL_SEND_INTERVAL = 0.1
# The subject for text notifications
TEXT_NOTIFICATION_SUBJECT = ''
# The text for text notifications (max length of 138 characters)
TEXT_NOTIFICATION_TEXT = 'One or more of your leases has a high percent chance of closing today, tomorrow, or in 2 days. Visit go.ncsu.edu/shellcast for details.'

NOTIFICATION_TYPE_EMAIL = 'email'
NOTIFICATION_TYPE_TEXT = 'text'

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

def sendNotificationsWithAWSSES(emailNotifications, textNotifications):
  # Create a new SES client
  client = boto3.client('ses', region_name=current_app.config['AWS_REGION'], aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'], aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'])
  curDate = datetime.now(pytz.timezone('US/Eastern')).strftime('%m/%d/%Y')
  emailNotificationSubject = SUBJECT_TEMPLATE.format(curDate)
  responses = []
  # send the email notifications
  for address, emailBodyChunks, userId in emailNotifications:
    body = ''.join(emailBodyChunks)
    sendSuccess, response = sendEmailWithAWSSES(client, address, emailNotificationSubject, body)
    responses.append((address, body, NOTIFICATION_TYPE_EMAIL, userId, sendSuccess, response))
    time.sleep(EMAIL_SEND_INTERVAL) # add a delay so that we don't exceed our max send rate (currently 14 emails/second)
  # send the text notifications
  for address, body, userId in textNotifications:
    sendSuccess, response = sendEmailWithAWSSES(client, address, TEXT_NOTIFICATION_SUBJECT, body)
    responses.append((address, body, NOTIFICATION_TYPE_TEXT, userId, sendSuccess, response))
    time.sleep(EMAIL_SEND_INTERVAL) # add a delay so that we don't exceed our max send rate (currently 14 emails/second)
  return responses

def probabilityToRisk(closureValue):
  flag = ""
  if(closureValue == 1):
    flag = "Very Low"
  elif(closureValue == 2):
    flag = "Low"
  elif(closureValue == 3):
    flag = "Moderate"
  elif(closureValue == 4):
    flag = "High"
  elif(closureValue == 5):
    flag = "Very High"
  return flag


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
  users = db.session.query(User).filter_by(deleted=False).all()
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
          leaseInfo = LEASE_TEMPLATE.format(lease.ncdmf_lease_id, probabilityToRisk(prob.prob_1d_perc), probabilityToRisk(prob.prob_2d_perc), probabilityToRisk(prob.prob_3d_perc))
          notificationText.append(leaseInfo)
          needToSendNotification = True
    # add a disclaimer to the end of the notifications
    notificationText.append(NOTIFICATION_FOOTER)

    if (needToSendNotification):
      # only send emails or texts depending on the user's preferences
      if (user.email_pref and emailAddress != None):
        emailNotificationsToSend.append((emailAddress, notificationText, user.id))
      if (user.text_pref and textAddress != None):
        textNotificationsToSend.append((textAddress, TEXT_NOTIFICATION_TEXT, user.id))

  # send notifications
  responses = sendNotificationsWithAWSSES(emailNotificationsToSend, textNotificationsToSend)
  # log all notifications that were sent
  for address, notificationText, notificationType, userId, sendSuccess, resText in responses:
    notification = Notification(address=address, notification_text=notificationText, notification_type=notificationType, user_id=userId, send_success=sendSuccess, response_text=resText)
    db.session.add(notification)
  db.session.commit()
  t1 = time.perf_counter_ns()
  result = 'Constructed and sent {} email notifications and {} text notifications to {} users in {} seconds'.format(len(emailNotificationsToSend), len(textNotificationsToSend), len(users), (t1 - t0) / 1000000000)
  logging.info(result)
  return result
