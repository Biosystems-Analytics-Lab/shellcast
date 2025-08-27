import pytest

from models.User import User
from models.PhoneServiceProvider import PhoneServiceProvider

from firebase_admin import auth

def test_deleteAccount(client, dbSession, addMockFbUser):
  # check to make sure that there are no users in the database
  results = dbSession.query(User).all()
  assert len(results) == 0

  # add a mobile service provider to the db
  provider = PhoneServiceProvider(name='Bleh Mobile', mms_gateway='mms.blah.com', sms_gateway='sms.blah.com')
  dbSession.add(provider)
  dbSession.commit()
  providerId = provider.id

  # add two mock Firebase users
  addMockFbUser(dict(uid='blah1', email='blah1@gmail.com'), 'validUser1')
  user1 = User(firebase_uid='blah1', email='blah1@gmail.com', phone_number='1234567890', service_provider_id=providerId, email_pref=True, text_pref=True, prob_pref=50)
  addMockFbUser(dict(uid='blah2', email='blah2@gmail.com'), 'validUser2')
  user2 = User(firebase_uid='blah2', email='blah2@gmail.com', phone_number='1234567890', service_provider_id=providerId, email_pref=True, text_pref=True, prob_pref=50)
  dbSession.add(user1)
  dbSession.add(user2)
  dbSession.commit()

  # make sure they're both in the db
  res = client.get('/userInfo', headers={'Authorization': 'validUser1'})
  assert res.status_code == 200
  res = client.get('/userInfo', headers={'Authorization': 'validUser2'})
  assert res.status_code == 200
  results = dbSession.query(User).all()
  assert len(results) == 2

  # delete the first user
  res = client.get('/deleteAccount', headers={'Authorization': 'validUser1'})
  assert res.status_code == 200
  userRes = dbSession.query(User).all()
  assert userRes[0].firebase_uid == None
  assert userRes[0].email == None
  assert userRes[0].phone_number == None
  assert userRes[0].service_provider_id == None
  assert userRes[0].email_pref == User.DEFAULT_email_pref
  assert userRes[0].text_pref == User.DEFAULT_text_pref
  assert userRes[0].prob_pref == User.DEFAULT_prob_pref
  assert userRes[0].deleted == True

  assert userRes[1].firebase_uid == 'blah2'
  assert userRes[1].email == 'blah2@gmail.com'
  assert userRes[1].phone_number == '1234567890'
  assert userRes[1].service_provider_id == providerId
  assert userRes[1].email_pref == True
  assert userRes[1].text_pref == True
  assert userRes[1].prob_pref == 50
  assert userRes[1].deleted == False

  # delete the second user
  res = client.get('/deleteAccount', headers={'Authorization': 'validUser2'})
  assert res.status_code == 200
  userRes = dbSession.query(User).all()
  assert userRes[0].firebase_uid == None
  assert userRes[0].email == None
  assert userRes[0].phone_number == None
  assert userRes[0].service_provider_id == None
  assert userRes[0].email_pref == User.DEFAULT_email_pref
  assert userRes[0].text_pref == User.DEFAULT_text_pref
  assert userRes[0].prob_pref == User.DEFAULT_prob_pref
  assert userRes[0].deleted == True

  assert userRes[1].firebase_uid == None
  assert userRes[1].email == None
  assert userRes[1].phone_number == None
  assert userRes[1].service_provider_id == None
  assert userRes[1].email_pref == User.DEFAULT_email_pref
  assert userRes[1].text_pref == User.DEFAULT_text_pref
  assert userRes[1].prob_pref == User.DEFAULT_prob_pref
  assert userRes[1].deleted == True


def test_deleteNonExistentUser(client, addMockFbUser):
  # add two mock Firebase users
  addMockFbUser(dict(uid='blah1', email='blah1@gmail.com'), 'validUser1')
  addMockFbUser(dict(uid='blah2', email='blah2@gmail.com'), 'validUser2')

  # try to delete another user
  res = client.get('/deleteAccount', headers={'Authorization': 'validUser3'})
  # the userRequired authentication code should prevent any of the deleteAccount code
  # from running and just return a 401
  assert res.status_code == 401

