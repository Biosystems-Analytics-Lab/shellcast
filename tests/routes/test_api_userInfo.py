import pytest

from models.User import User
from models.Lease import Lease
from models.ClosureProbability import ClosureProbability

from firebase_admin import auth

def test_valid(client, dbSession, addMockFbUser):
  # check to make sure that there are no users in the database
  results = dbSession.query(User).all()
  assert len(results) == 0

  # add a mock Firebase user
  addMockFbUser(dict(uid='blah', email='blah@gmail.com', phone_number='11234567890', display_name='Blah Bleh'), 'validUser1')

  # request user info
  res = client.get('/userInfo', headers={'Authorization': 'validUser1'})
  assert res.status_code == 200
  json = res.get_json()
  assert len(json) == 2
  assert json.get('firebase_uid') == None
  assert json.get('first_name') == None
  assert json.get('last_name') == None
  assert json.get('sms_pref') == None
  assert json.get('email_pref') == None
  assert json['phone_number'] == '11234567890'
  assert json['email'] == 'blah@gmail.com'

  # check that the user is now created in the database
  results = dbSession.query(User).all()
  assert len(results) == 1

  # make another request for the same user's info
  res = client.get('/userInfo', headers={'Authorization': 'validUser1'})
  assert res.status_code == 200
  json = res.get_json()
  assert len(json) == 2
  assert json.get('firebase_uid') == None
  assert json.get('first_name') == None
  assert json.get('last_name') == None
  assert json.get('sms_pref') == None
  assert json.get('email_pref') == None
  assert json['phone_number'] == '11234567890'
  assert json['email'] == 'blah@gmail.com'

  # check that the user is not created again
  results = dbSession.query(User).all()
  assert len(results) == 1

def test_invalidToken(client, addMockFbUser):
  # add a mock Firebase user
  addMockFbUser(dict(uid='blah', email='blah@gmail.com', phone_number='11234567890', display_name='Blah Bleh'), 'validUser1')

  res = client.get('/userInfo', headers={'Authorization': 'invalidUser'})
  assert res.status_code == 401

def test_expiredToken(client, addMockFbUser):
  # add a mock Firebase user
  addMockFbUser(dict(uid='blah', email='blah@gmail.com', phone_number='11234567890', display_name='Blah Bleh'), 'validUser1', True)

  res = client.get('/userInfo', headers={'Authorization': 'validUser1'})
  assert res.status_code == 401
