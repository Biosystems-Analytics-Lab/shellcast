import logging
import time
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timezone
import pytz
import boto3
from botocore.exceptions import ClientError

from models import db
from models.User import User
from models.ClosureProbability import ClosureProbability
from models.Lease import Lease
from models.Notification import Notification

from routes.authentication import cronOnly

# The address that all emails are sent from.
# This address must be verified with Amazon SES.
SENDER = 'ShellCast <shellcastapp@ncsu.edu>'
# The subject line template for all emails.
SUBJECT_TEMPLATE = 'ShellCast Lease Closure Probabilities for {}'
# The character encoding for all emails.
CHARSET = 'UTF-8'
# The template for lease information in notifications.
LEASE_TEMPLATE =  'Lease: {}\n  1-day: {}%\n  2-day: {}%\n  3-day: {}%\n'



VERIFIED_ADDRESSES = ['shellcastapp@ncsu.edu', 'stparham@ncsu.edu', 'ssaia@ncsu.edu', 'nnelson4@ncsu.edu']

cron = Blueprint('cron', __name__)

def sendNotificationsWithAWSSES(emails):
  # Create a new SES client
  client = boto3.client('ses', region_name=current_app.config['AWS_REGION'], aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'], aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'])
  curDate = datetime.now(pytz.timezone('US/Eastern')).strftime('%B %d, %Y')
  subject = SUBJECT_TEMPLATE.format(curDate)
  responses = []
  for address, body, userId in emails:
    if (address in VERIFIED_ADDRESSES): # TODO remove this check after moving out of SES sandbox
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
        responses.append((address, body, userId, False, e.response['Error']['Message']))
      else:
        logging.info('Email successfully sent to ' + address)
        logging.info(response['MessageId'])
        responses.append((address, body, userId, True, response['MessageId']))
    else:
      print('Email {} not verified, so can\'t send until out of SES sandbox'.format(address))
    time.sleep(1.1) # TODO remove this after moving out of SES sandbox
  return responses

@cron.route('/sendNotifications')
@cronOnly
def sendNotifications():
  """
  Sends notifications to all users whose leases warrant a notification.
  """
  logging.info('Constructing and sending notifications...')
  t0 = time.perf_counter_ns()
  notificationsToSend = []
  # for each user
  users = db.session.query(User).all()
  for user in users:
    # get email address
    emailAddress = user.email
    # get phone number and service provider gateway
    textAddress = None
    if (user.phone_number != None and user.service_provider_id != None):
      textAddress = '{}@{}'.format(user.phone_number, user.service_provider.mms_gateway)
    # construct notification text
    emailNotification = 'https://ncsu-shellcast.appspot.com/\n'
    textNotification = 'https://ncsu-shellcast.appspot.com/\n'
    needToSendEmail = False
    needToSendText = False
    # for each lease
    for lease in user.leases:
      # if the user has not deleted the lease and they want to receive some kind of notification
      if (not lease.deleted_by_user and (lease.email_pref or lease.text_pref)):
        if (len(lease.closureProbabilities) >= 1):
          # get the latest closure probability for the lease
          prob = lease.closureProbabilities[0]
          # if any of the day probs are >= the lease's prob preference
          if (prob.prob_1d_perc >= lease.prob_pref or prob.prob_2d_perc >= lease.prob_pref or prob.prob_3d_perc >= lease.prob_pref):
            text = LEASE_TEMPLATE.format(lease.ncdmf_lease_id, prob.prob_1d_perc, prob.prob_2d_perc, prob.prob_3d_perc)
            if (lease.email_pref):
              emailNotification += text
              needToSendEmail = True
            if (lease.text_pref):
              textNotification += text
              needToSendText = True
    if (needToSendEmail and emailAddress != None):
      notificationsToSend.append((emailAddress, emailNotification, user.id))
    if (needToSendText and textAddress != None):
      notificationsToSend.append((textAddress, textNotification, user.id))

  # send notifications
  responses = sendNotificationsWithAWSSES(notificationsToSend)
  # log all notifications that were sent
  for address, notificationText, userId, sendSuccess, resText in responses:
    notification = Notification(address=address, notification_text=notificationText, user_id=userId, send_success=sendSuccess, response_text=resText)
    db.session.add(notification)
  db.session.commit()
  t1 = time.perf_counter_ns()
  result = 'Constructed and sent {} notifications to {} users in {} seconds'.format(len(notificationsToSend), len(users), (t1 - t0) / 1000000000)
  logging.info(result)
  return result
