import pytest

from models.User import User

def test_User(dbSession):
  validUser1 = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='asdf@adf.com', phone_number='11234567890', first_name='as', last_name='df')

  dbSession.add(validUser1)
  dbSession.commit()

  assert validUser1.id == 1

  res = User.query.all()

  assert len(res) == 1
  assert res[0].firebase_uid == validUser1.firebase_uid
  assert res[0].sms_pref == False
  assert res[0].email_pref == False
