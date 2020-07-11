import pytest

from models.User import User
from models.Lease import Lease
from models.ClosureProbability import ClosureProbability

from firebase_admin import auth

def test_search_leases(client, dbSession, addMockFbUser):
  # add a mock Firebase user
  addMockFbUser(dict(uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com', phone_number='11234567890'), 'validUser1')

  # add the user to the db
  user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com', phone_number='11234567890')
  dbSession.add(user)
  dbSession.commit()

  res = client.post('/searchLeases', headers={'Authorization': 'validUser1'}, json={'search': '1'})
  assert res.status_code == 200

  json = res.get_json()
  assert len(json) == 2

  assert json[0] == '819401'
  assert json[1] == '123456'
