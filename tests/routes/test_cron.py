import pytest

from models.PhoneServiceProvider import PhoneServiceProvider
from models.User import User
from models.CMUProbability import CMUProbability
from models.UserLease import UserLease
from models.Notification import Notification

from routes.cron import sendNotificationsWithAWSSES, NOTIFICATION_HEADER, LEASE_TEMPLATE, NOTIFICATION_FOOTER

def test_sendNotificationsWithAWSSES(app, monkeyPatchBotoClient):
  with app.app_context():
    emailNotificationsToSend = [
      ('blah@ncsu.edu', ['EmailNotification1'], 1),
      ('shellcastapp@ncsu.edu', ['EmailNotification2'], 2),
      ('ethedla@ncsu.edu', ['EmailNotification3'], 3),
    ]
    textNotificationsToSend = [
      ('1234567890@sms.blah.com', 'SMSNotification1', 1),
      ('5555555555@sms.blah.com', 'SMSNotification2', 2),
      ('0987654321@sms.blah.com', 'SMSNotification3', 3),
    ]

    responses = sendNotificationsWithAWSSES(emailNotificationsToSend, textNotificationsToSend)

    assert responses[0] == ('blah@ncsu.edu', 'EmailNotification1', 'email', 1, True, 'abc123')
    assert responses[1] == ('shellcastapp@ncsu.edu', 'EmailNotification2', 'email', 2, True, 'abc123')
    assert responses[2] == ('bleh3@ncsu.edu', 'EmailNotification3', 'email', 3, True, 'abc123')
    assert responses[3] == ('1234567890@sms.blah.com', 'SMSNotification1', 'text', 1, True, 'abc123')
    assert responses[4] == ('5555555555@sms.blah.com', 'SMSNotification2', 'text', 2, True, 'abc123')
    assert responses[5] == ('0987654321@sms.blah.com', 'SMSNotification3', 'text', 3, True, 'abc123')

def test_sendNotifications(client, dbSession, monkeyPatchBotoClient):
  # add a service provider to the db
  provider = PhoneServiceProvider(name='Verizon', mms_gateway='vzwpix.com', sms_gateway='vtext.com')
  dbSession.add(provider)
  dbSession.commit()

  # add a user to the db
  user = User(
    firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1',
    email='shellcastapp@ncsu.edu',
    phone_number='5555555555',
    service_provider_id=1,
    email_pref=True,
    text_pref=False,
    prob_pref=50
  )
  dbSession.add(user)
  dbSession.commit()

  # add a few leases for the user
  leases = [
    UserLease(user_id=user.id, ncdmf_lease_id='45678', grow_area_name='A01', cmu_name='U001', rainfall_thresh_in=1.5, geometry=(34.404497, -77.567573)),
    UserLease(user_id=user.id, ncdmf_lease_id='12345', grow_area_name='B02', cmu_name='U002', rainfall_thresh_in=2.5, geometry=(35.207332, -76.523872)),
    UserLease(user_id=user.id, ncdmf_lease_id='82945', grow_area_name='C01', cmu_name='U003', rainfall_thresh_in=1.5, geometry=(36.164344, -75.927864))
  ]
  dbSession.add_all(leases)
  dbSession.commit()

  # add some closure probabilities for those leases
  probabilities = [
    CMUProbability(cmu_name='U001', prob_1d_perc=1, prob_2d_perc=4, prob_3d_perc=4),
    CMUProbability(cmu_name='U002', prob_1d_perc=2, prob_2d_perc=4, prob_3d_perc=4),
    CMUProbability(cmu_name='U003', prob_1d_perc=2, prob_2d_perc=3, prob_3d_perc=2)
  ]
  dbSession.add_all(probabilities)
  dbSession.commit()

  # make a request to send notifications (without the cron service identifying header)
  res = client.get('/sendNotifications')
  assert res.status_code == 401

  # make a request to send notifications (and look like a cron service)
  res = client.get('/sendNotifications', headers={'X-Appengine-Cron': True})
  assert res.status_code == 200

  data = str(res.get_data())
  assert '1 email notifications' in data
  assert '0 text notifications' in data
  assert '1 users' in data

  # check if a notification log record was added
  results = dbSession.query(Notification).all()
  assert len(results) == 1
  assert 'https://go.ncsu.edu/shellcast' in results[0].notification_text
  assert 'Lease: 45678' in results[0].notification_text
  assert 'Today: Very Low' in results[0].notification_text
  assert 'Tomorrow: High' in results[0].notification_text
  assert 'In 2 days: High' in results[0].notification_text
  assert not 'Lease: 12345' in results[0].notification_text
  assert 'Lease: 82945' in results[0].notification_text
  assert 'Today: Low' in results[0].notification_text
  assert 'Tomorrow: Moderate' in results[0].notification_text
  assert 'In 2 days: Low' in results[0].notification_text
  assert 'These predictions are in no way indicative of whether or not a lease will actually be temporarily closed for harvest.' in results[0].notification_text
  assert 'email' == results[0].notification_type

  # turn off email_pref and turn on text_pref
  user.email_pref = False
  user.text_pref = True
  dbSession.add(user)
  dbSession.commit()

  # make a request to send notifications
  res = client.get('/sendNotifications', headers={'X-Appengine-Cron': True})
  assert res.status_code == 200

  data = str(res.get_data())
  assert '0 email notifications' in data
  assert '1 text notifications' in data
  assert '1 users' in data

  # check if a notification log record was added
  results = dbSession.query(Notification).all()
  assert len(results) == 2
  assert 'One or more of your leases has a high percent chance of closing today, tomorrow, or in 2 days. Visit go.ncsu.edu/shellcast for details.' == results[1].notification_text
  assert 'text' == results[1].notification_type

def test_sendNotifications_deleted_users(client, dbSession, monkeyPatchBotoClient):
  # add a user and deleted user to the db
  user = User(
    firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1',
    email='shellcastapp@ncsu.edu',
    email_pref=True,
    text_pref=False,
    prob_pref=50
  )
  deletedUser = User(
    deleted=True
  )
  dbSession.add(user)
  dbSession.commit()

  # add a few leases for the user
  leases = [
    UserLease(user_id=user.id, ncdmf_lease_id='45678', grow_area_name='A01', cmu_name='U001', rainfall_thresh_in=1.5, geometry=(34.404497, -77.567573)),
    UserLease(user_id=user.id, ncdmf_lease_id='12345', grow_area_name='B02', cmu_name='U002', rainfall_thresh_in=2.5, geometry=(35.207332, -76.523872)),
    UserLease(user_id=user.id, ncdmf_lease_id='82945', grow_area_name='C01', cmu_name='U003', rainfall_thresh_in=1.5, geometry=(36.164344, -75.927864))
  ]
  dbSession.add_all(leases)
  dbSession.commit()

  # add some closure probabilities for those leases
  probabilities = [
    CMUProbability(cmu_name='U001', prob_1d_perc=1, prob_2d_perc=4, prob_3d_perc=4),
    CMUProbability(cmu_name='U002', prob_1d_perc=2, prob_2d_perc=4, prob_3d_perc=4),
    CMUProbability(cmu_name='U003', prob_1d_perc=2, prob_2d_perc=3, prob_3d_perc=2)
  ]
  dbSession.add_all(probabilities)
  dbSession.commit()

  # make a request to send notifications
  res = client.get('/sendNotifications', headers={'X-Appengine-Cron': True})
  assert res.status_code == 200

  # make sure that only 1 user was sent notifications
  data = str(res.get_data())
  assert '1 users' in data