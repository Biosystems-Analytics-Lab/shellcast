import pytest

from models.User import User
from models.Lease import Lease
from models.ClosureProbability import ClosureProbability
from models.Notification import Notification

def test_valid(dbSession):
  user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='asdf@adf.com', phone_number='11234567890')

  dbSession.add(user)
  dbSession.commit()

  lease = Lease(user_id=user.id, ncdmf_lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5, window_pref=1, prob_pref=50)

  dbSession.add(lease)
  dbSession.commit()

  prob = ClosureProbability(lease_id=lease.id, rain_forecast_1d_in=2, rain_forecast_2d_in=3.2, rain_forecast_3d_in=4.5, prob_1d_perc=60, prob_2d_perc=70, prob_3d_perc=80)
  
  dbSession.add(prob)
  dbSession.commit()

  notification = Notification(user_id=user.id, closure_prob_id=prob.id, notification_text='There is a 54%% chance that your lease will be closed within 1 day.')

  dbSession.add(notification)
  dbSession.commit()

  assert notification.id == 1

  res = Notification.query.all()

  assert len(res) == 1
  assert res[0].user_id == notification.user_id
  assert res[0].closure_prob_id == notification.closure_prob_id
  assert res[0].notification_text == notification.notification_text
  assert res[0].send_success == True

def test_asDict():
  notification = Notification(user_id=1, closure_prob_id=1, notification_text='There is a 54%% chance that your lease will be closed within 1 day.')

  dictForm = notification.asDict()

  assert dictForm['notification_text'] == notification.notification_text
  assert dictForm['send_success'] == notification.send_success

def test_repr():
  notification = Notification(user_id=1, closure_prob_id=1, notification_text='There is a 54%% chance that your lease will be closed within 1 day.')

  stringForm = notification.__repr__()

  assert 'Notification' in stringForm
  assert str(notification.user_id) in stringForm
  assert str(notification.closure_prob_id) in stringForm
  assert notification.notification_text in stringForm
