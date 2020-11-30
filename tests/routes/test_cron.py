import pytest

from models.User import User
from models.CMUProbability import CMUProbability
from models.UserLease import UserLease
from models.Notification import Notification

from routes.cron import sendNotificationsWithAWSSES, NOTIFICATION_HEADER, LEASE_TEMPLATE, NOTIFICATION_FOOTER

def test_sendNotificationsWithAWSSES(app, monkeyPatchBotoClient):
  with app.app_context():
    emailNotificationsToSend = [
      ('blah@ncsu.edu', ['Notification1'], 1),
      ('shellcastapp@ncsu.edu', ['Notification2'], 2),
      ('bleh3@ncsu.edu', ['Notification3'], 3),
    ]
    textNotificationsToSend = [
      ('1234567890@sms.blah.com', ['Notification1'], 1),
      ('5555555555@sms.blah.com', ['Notification2'], 2),
      ('0987654321@sms.blah.com', ['Notification3'], 3),
    ]

    responses = sendNotificationsWithAWSSES(emailNotificationsToSend, textNotificationsToSend)

    assert responses[0] == ('blah@ncsu.edu', 'Notification1', 1, True, 'abc123')
    assert responses[1] == ('shellcastapp@ncsu.edu', 'Notification2', 2, True, 'abc123')
    assert responses[2] == ('bleh3@ncsu.edu', 'Notification3', 3, True, 'abc123')
    assert responses[3] == ('1234567890@sms.blah.com', 'Notification1', 1, True, 'abc123')
    assert responses[4] == ('5555555555@sms.blah.com', 'Notification2', 2, True, 'abc123')
    assert responses[5] == ('0987654321@sms.blah.com', 'Notification3', 3, True, 'abc123')

def test_sendVariedSizeTextNotifications(app, monkeyPatchBotoClient, genRandomString):
  with app.app_context():
    emails = []
    texts = [
      (
        '0000000000@sms.blah.com',
        [genRandomString(length=34), genRandomString(length=45)], # should be sent as 1 email
        1
      ),
      (
        '0000000001@sms.blah.com',
        [genRandomString(length=119), genRandomString(length=1)], # should be sent as 1 email
        2
      ),
      (
        '0000000002@sms.blah.com',
        [genRandomString(length=119), genRandomString(length=2)], # should be sent as 2 emails
        3
      ),
      (
        '0000000003@sms.blah.com',
        [
          genRandomString(length=34), genRandomString(length=45), genRandomString(length=21),
          genRandomString(length=40), genRandomString(length=40), genRandomString(length=20)
        ], # should be sent as 2 emails
        4
      ),
      (
        '0000000004@sms.blah.com',
        [
          genRandomString(length=20), genRandomString(length=55), genRandomString(length=55),
          genRandomString(length=55), genRandomString(length=55), genRandomString(length=20)
        ], # should be sent as 3 emails
        5
      ),
    ]

    responses = sendNotificationsWithAWSSES(emails, texts)

    # check that all the responses are correct
    for i in range(len(responses)):
      assert responses[i][0] == texts[i][0]
      assert responses[i][1] == ''.join(texts[i][1])
      assert responses[i][2] == texts[i][2]

    # check that the texts were broken up into emails appropriately
    emailsTo0 = monkeyPatchBotoClient()['0000000000@sms.blah.com']
    assert len(emailsTo0) == 1
    assert emailsTo0[0]['body'] == ''.join(texts[0][1])

    emailsTo1 = monkeyPatchBotoClient()['0000000001@sms.blah.com']
    assert len(emailsTo1) == 1
    assert emailsTo1[0]['body'] == ''.join(texts[1][1])

    emailsTo2 = monkeyPatchBotoClient()['0000000002@sms.blah.com']
    assert len(emailsTo2) == 2
    assert emailsTo2[0]['body'] == texts[2][1][0]
    assert emailsTo2[1]['body'] == texts[2][1][1]

    emailsTo3 = monkeyPatchBotoClient()['0000000003@sms.blah.com']
    assert len(emailsTo3) == 2
    assert emailsTo3[0]['body'] == ''.join(texts[3][1][0:3])
    assert emailsTo3[1]['body'] == ''.join(texts[3][1][3:6])

    emailsTo4 = monkeyPatchBotoClient()['0000000004@sms.blah.com']
    assert len(emailsTo4) == 3
    assert emailsTo4[0]['body'] == ''.join(texts[4][1][0:2])
    assert emailsTo4[1]['body'] == ''.join(texts[4][1][2:4])
    assert emailsTo4[2]['body'] == ''.join(texts[4][1][4:6])

def test_sendNotifications(client, dbSession, monkeyPatchBotoClient):
  # add a user to the db
  user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='shellcastapp@ncsu.edu', email_pref=True, prob_pref=50)
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
    CMUProbability(cmu_name='U001', prob_1d_perc=60, prob_2d_perc=70, prob_3d_perc=80),
    CMUProbability(cmu_name='U002', prob_1d_perc=45, prob_2d_perc=49, prob_3d_perc=49),
    CMUProbability(cmu_name='U003', prob_1d_perc=32, prob_2d_perc=33, prob_3d_perc=69)
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
  assert '1-day: 60%' in results[0].notification_text
  assert '2-day: 70%' in results[0].notification_text
  assert '3-day: 80%' in results[0].notification_text
  assert not 'Lease: 12345' in results[0].notification_text
  assert 'Lease: 82945' in results[0].notification_text
  assert '1-day: 32%' in results[0].notification_text
  assert '2-day: 33%' in results[0].notification_text
  assert '3-day: 69%' in results[0].notification_text
  assert 'These predictions are in no way indicative of whether or not a growing area will actually be temporarily closed for harvest.' in results[0].notification_text
