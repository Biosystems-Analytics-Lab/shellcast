import pytest

from models.User import User
from models.ClosureProbability import ClosureProbability
from models.Lease import Lease
from models.Notification import Notification

from routes.cron import sendNotificationsWithAWSSES

def test_sendNotificationsWithAWSSES(app, monkeyPatchBotoClient):
  with app.app_context():
    notificationsToSend = [
      ('blah@ncsu.edu', 'Notification1', 1),
      ('shellcastapp@ncsu.edu', 'Notification2', 2),
      ('bleh3@ncsu.edu', 'Notification3', 3),
    ]

    responses = sendNotificationsWithAWSSES(notificationsToSend)

    assert responses[0] == ('blah@ncsu.edu', 'Notification1', 1, True, 'bleh')
    assert responses[1] == ('shellcastapp@ncsu.edu', 'Notification2', 2, True, 'bleh')
    assert responses[2] == ('bleh3@ncsu.edu', 'Notification3', 3, True, 'bleh')

def test_sendNotifications(client, dbSession, monkeyPatchBotoClient):
  # add a user to the db
  user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='shellcastapp@ncsu.edu')
  dbSession.add(user)
  dbSession.commit()

  # add a few leases for the user
  leases = [
    Lease(user_id=user.id, ncdmf_lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5, geometry=(34.404497, -77.567573), email_pref=True, prob_pref=50),
    Lease(user_id=user.id, ncdmf_lease_id='12345', grow_area_name='B02', rainfall_thresh_in=2.5, geometry=(35.207332, -76.523872), email_pref=True, prob_pref=75),
    Lease(user_id=user.id, ncdmf_lease_id='82945', grow_area_name='C01', rainfall_thresh_in=1.5, geometry=(36.164344, -75.927864), email_pref=True, prob_pref=50)
  ]
  dbSession.add_all(leases)
  dbSession.commit()

  # add some closure probabilities for those leases
  probabilities = [
    ClosureProbability(lease_id=leases[0].id, prob_1d_perc=60, prob_2d_perc=70, prob_3d_perc=80),
    ClosureProbability(lease_id=leases[1].id, prob_1d_perc=45, prob_2d_perc=54, prob_3d_perc=57),
    ClosureProbability(lease_id=leases[2].id, prob_1d_perc=32, prob_2d_perc=33, prob_3d_perc=69)
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
  assert '1 notifications' in data
  assert '1 users' in data

  # check if a notification log record was added
  results = dbSession.query(Notification).all()
  assert len(results) == 1
  assert 'Lease: 45678' in results[0].notification_text
  assert '1-day: 60%' in results[0].notification_text
  assert '2-day: 70%' in results[0].notification_text
  assert '3-day: 80%' in results[0].notification_text
  assert not 'Lease: 12345' in results[0].notification_text
  assert 'Lease: 82945' in results[0].notification_text
  assert '1-day: 32%' in results[0].notification_text
  assert '2-day: 33%' in results[0].notification_text
  assert '3-day: 69%' in results[0].notification_text
