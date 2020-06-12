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

def test_asDict(genRandomString):
  user = User(firebase_uid=genRandomString(length=28), email=genRandomString(length=13), phone_number=genRandomString(length=11), first_name=genRandomString(length=10), last_name=genRandomString(length=10))

  dictForm = user.asDict()

  assert dictForm['firebase_uid'] == user.firebase_uid
  assert dictForm['first_name'] == user.first_name
  assert dictForm['last_name'] == user.last_name
  assert dictForm['phone_number'] == user.phone_number
  assert dictForm['email'] == user.email
  assert dictForm['sms_pref'] == user.sms_pref
  assert dictForm['email_pref'] == user.email_pref

def test_repr(genRandomString):
  user = User(firebase_uid=genRandomString(length=28), email=genRandomString(length=13), phone_number=genRandomString(length=11), first_name=genRandomString(length=10), last_name=genRandomString(length=10))

  stringForm = user.__repr__()

  assert 'User' in stringForm
  assert user.email in stringForm
