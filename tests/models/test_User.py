import pytest

from models.User import User
from models.PhoneServiceProvider import PhoneServiceProvider

def test_User(dbSession):
  provider = PhoneServiceProvider(name='Verizon', mms_gateway='vzwpix.com')

  dbSession.add(provider)
  dbSession.commit()

  validUser1 = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='asdf@adf.com', phone_number='1234567890', service_provider_id=provider.id)

  dbSession.add(validUser1)
  dbSession.commit()

  assert validUser1.id == 1

  res = User.query.all()

  assert len(res) == 1
  assert res[0].firebase_uid == validUser1.firebase_uid
  assert res[0].email == validUser1.email
  assert res[0].phone_number == validUser1.phone_number

def test_asDict(genRandomString):
  user = User(firebase_uid=genRandomString(length=28), email=genRandomString(length=13), phone_number=genRandomString(length=11))

  dictForm = user.asDict()

  assert dictForm['firebase_uid'] == user.firebase_uid
  assert dictForm['phone_number'] == user.phone_number
  assert dictForm['email'] == user.email

def test_repr(genRandomString):
  user = User(firebase_uid=genRandomString(length=28), email=genRandomString(length=13), phone_number=genRandomString(length=11))

  stringForm = user.__repr__()

  assert 'User' in stringForm
  assert user.email in stringForm
