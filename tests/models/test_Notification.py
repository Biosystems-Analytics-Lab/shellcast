import pytest

from models.User import User
from models.Notification import Notification

def test_valid(dbSession):
  user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='asdf@adf.com', phone_number='11234567890')

  dbSession.add(user)
  dbSession.commit()

  notification = Notification(user_id=user.id, address='asdf@adf.com', notification_text='There is a 54%% chance that your lease will be closed within 1 day.', notification_type='email')

  dbSession.add(notification)
  dbSession.commit()

  assert notification.id == 1

  res = Notification.query.all()

  assert len(res) == 1
  assert res[0].user_id == notification.user_id
  assert res[0].notification_text == notification.notification_text
  assert res[0].send_success == True

def test_asDict():
  notification = Notification(user_id=1, notification_text='There is a 54%% chance that your lease will be closed within 1 day.')

  dictForm = notification.asDict()

  assert dictForm['notification_text'] == notification.notification_text
  assert dictForm['send_success'] == notification.send_success

def test_repr():
  notification = Notification(user_id=1, notification_text='There is a 54%% chance that your lease will be closed within 1 day.')

  stringForm = notification.__repr__()

  assert 'Notification' in stringForm
  assert str(notification.user_id) in stringForm
  assert notification.notification_text in stringForm
