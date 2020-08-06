import pytest

from models.User import User
from models.PhoneServiceProvider import PhoneServiceProvider

from firebase_admin import auth

def test_valid(client, dbSession, addMockFbUser):
  # check to make sure that there are no users in the database
  results = dbSession.query(User).all()
  assert len(results) == 0

  # add a mock Firebase user
  addMockFbUser(dict(uid='blah', email='blah@gmail.com'), 'validUser1')

  # request user info
  res = client.get('/userInfo', headers={'Authorization': 'validUser1'})
  assert res.status_code == 200
  json = res.get_json()
  assert len(json) == 1
  assert json['email'] == 'blah@gmail.com'
  assert json.get('phone_number') == None
  assert json.get('service_provider_id') == None

  # check that the user is now created in the database
  results = dbSession.query(User).all()
  assert len(results) == 1

  # make another request for the same user's info
  res = client.get('/userInfo', headers={'Authorization': 'validUser1'})
  assert res.status_code == 200
  json = res.get_json()
  assert len(json) == 1
  assert json['email'] == 'blah@gmail.com'
  assert json.get('phone_number') == None
  assert json.get('service_provider_id') == None

  # check that the user is not created again
  results = dbSession.query(User).all()
  assert len(results) == 1
  user = results[0]

  # add a phone number and service provider for the user
  # add a mobile service provider to the db
  provider = PhoneServiceProvider(name='Bleh Mobile', mms_gateway='mms.blah.com')
  dbSession.add(provider)
  dbSession.commit()

  # update the user with a phone number and service provider id
  user.phone_number = '1234567890'
  user.service_provider_id = provider.id
  dbSession.add(user)
  dbSession.commit()

  # make another request for the same user's info
  res = client.get('/userInfo', headers={'Authorization': 'validUser1'})
  assert res.status_code == 200
  json = res.get_json()
  assert len(json) == 3
  assert json['email'] == 'blah@gmail.com'
  assert json['phone_number'] == '1234567890'
  assert json['service_provider_id'] == 1

def test_invalidToken(client, addMockFbUser):
  # add a mock Firebase user
  addMockFbUser(dict(uid='blah', email='blah@gmail.com'), 'validUser1')

  res = client.get('/userInfo', headers={'Authorization': 'invalidUser'})
  assert res.status_code == 401

def test_expiredToken(client, addMockFbUser):
  # add a mock Firebase user
  addMockFbUser(dict(uid='blah', email='blah@gmail.com'), 'validUser1', True)

  res = client.get('/userInfo', headers={'Authorization': 'validUser1'})
  assert res.status_code == 401

def test_update_info(client, addMockFbUser, dbSession):
  # add a mock Firebase user
  addMockFbUser(dict(uid='blah', email='blah@gmail.com'), 'validUser1')

  # add a mobile service provider
  provider = PhoneServiceProvider(name='Bleh Mobile', mms_gateway='mms.blah.com')
  dbSession.add(provider)
  dbSession.commit()

  # request user info
  res = client.get('/userInfo', headers={'Authorization': 'validUser1'})
  assert res.status_code == 200
  json = res.get_json()
  assert json['email'] == 'blah@gmail.com'

  # make a request to update the user's info
  res = client.post('/userInfo', headers={'Authorization': 'validUser1'}, json={'email': 'secondemail@gmail.com', 'phone_number': '5555555555', 'service_provider_id': 1})
  print(res.get_json())
  assert res.status_code == 200
  
  # check that the user's info is updated
  res = client.get('/userInfo', headers={'Authorization': 'validUser1'})
  assert res.status_code == 200
  json = res.get_json()
  assert json['phone_number'] == '5555555555'
  assert json['service_provider_id'] == 1
  assert json['email'] == 'secondemail@gmail.com'

def test_update_invalid_email(client, addMockFbUser):
  # add a mock Firebase user
  addMockFbUser(dict(uid='blah', email='blah@gmail.com'), 'validUser1')

  # make a request to update the user's info with an invalid email
  res = client.post('/userInfo', headers={'Authorization': 'validUser1'}, json={'email': 'myemail'})
  assert res.status_code == 400
  
  # check that the user's info is not updated
  res = client.get('/userInfo', headers={'Authorization': 'validUser1'})
  assert res.status_code == 200
  json = res.get_json()
  assert json['email'] == 'blah@gmail.com'

def test_update_invalid_phone(client, addMockFbUser, dbSession):
  # add a mock Firebase user
  addMockFbUser(dict(uid='blah', email='blah@gmail.com'), 'validUser1')

  # add a mobile service provider
  provider = PhoneServiceProvider(name='Bleh Mobile', mms_gateway='mms.blah.com')
  dbSession.add(provider)
  dbSession.commit()

  # make a request to update the user's info with an invalid phone number
  res = client.post('/userInfo', headers={'Authorization': 'validUser1'}, json={'phone_number': '123456789', 'service_provider_id': provider.id})
  assert res.status_code == 400
  
  # check that the user's info is not updated
  res = client.get('/userInfo', headers={'Authorization': 'validUser1'})
  assert res.status_code == 200
  json = res.get_json()
  assert json.get('phone_number') == None
  assert json['email'] == 'blah@gmail.com'
