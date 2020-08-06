import pytest

from models.User import User
from models.Lease import Lease
from models.NCDMFLease import NCDMFLease
from models.ClosureProbability import ClosureProbability

from firebase_admin import auth

def test_get_leases(client, dbSession, addMockFbUser):
  # add a mock Firebase user
  addMockFbUser(dict(uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com', phone_number='1234567890'), 'validUser1')

  # add the user to the db
  user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com', phone_number='1234567890')

  dbSession.add(user)
  dbSession.commit()

  # add some leases to the database
  leases = [
    Lease(user_id=user.id, ncdmf_lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5, geometry=(34.404497, -77.567573)),
    Lease(user_id=user.id, ncdmf_lease_id='12345', grow_area_name='B02', rainfall_thresh_in=2.5, geometry=(35.207332, -76.523872)),
    Lease(user_id=user.id, ncdmf_lease_id='82945', grow_area_name='C01', rainfall_thresh_in=1.5, geometry=(36.164344, -75.927864))
  ]

  dbSession.add_all(leases)
  dbSession.commit()

  res = client.get('/leases', headers={'Authorization': 'validUser1'})
  assert res.status_code == 200

  json = res.get_json()
  assert len(json) == 3

  assert json[0]['ncdmf_lease_id'] == '45678'
  assert json[0]['grow_area_name'] == 'A01'
  assert json[0]['rainfall_thresh_in'] == 1.5
  assert json[0]['geometry'] == [34.404497, -77.567573]
  assert json[1]['ncdmf_lease_id'] == '12345'
  assert json[1]['grow_area_name'] == 'B02'
  assert json[1]['rainfall_thresh_in'] == 2.5
  assert json[1]['geometry'] == [35.207332, -76.523872]
  assert json[2]['ncdmf_lease_id'] == '82945'
  assert json[2]['grow_area_name'] == 'C01'
  assert json[2]['rainfall_thresh_in'] == 1.5
  assert json[2]['geometry'] == [36.164344, -75.927864]

def test_add_lease(client, dbSession, addMockFbUser):
  # add a mock Firebase user
  addMockFbUser(dict(uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com'), 'validUser1')

  # add the user to the db
  user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com')
  dbSession.add(user)
  dbSession.commit()

  # add one existing lease for the user
  lease = Lease(user_id=user.id, ncdmf_lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5, geometry=(34.404497, -77.567573))
  dbSession.add(lease)
  dbSession.commit()

  # add some NCDMF leases
  ncdmfLeases = [
    NCDMFLease(ncdmf_lease_id='819401', grow_area_name='D11', rainfall_thresh_in=2.5, geometry=(34.404497, -77.567573)),
    NCDMFLease(ncdmf_lease_id='123456', grow_area_name='B05', rainfall_thresh_in=3.5, geometry=(35.923741, -76.239482)),
    NCDMFLease(ncdmf_lease_id='4-C-89', grow_area_name='A01', rainfall_thresh_in=1.5, geometry=(36.303915, -75.864693))
  ]
  dbSession.add_all(ncdmfLeases)
  dbSession.commit()

  # make a request to add the given lease
  res = client.post('/leases', headers={'Authorization': 'validUser1'}, json={'ncdmf_lease_id': '4-C-89'})
  assert res.status_code == 200

  json = res.get_json()

  assert json['ncdmf_lease_id'] == '4-C-89'
  assert json['grow_area_name'] == 'A01'
  assert json['rainfall_thresh_in'] == 1.5
  assert json['geometry'] == [36.303915, -75.864693]

  # get the user's leases
  res = client.get('/leases', headers={'Authorization': 'validUser1'})
  assert res.status_code == 200

  json = res.get_json()
  assert len(json) == 2
  assert json[0]['ncdmf_lease_id'] == '45678'
  assert json[0]['grow_area_name'] == 'A01'
  assert json[0]['rainfall_thresh_in'] == 1.5
  assert json[0]['geometry'] == [34.404497, -77.567573]
  assert json[1]['ncdmf_lease_id'] == '4-C-89'
  assert json[1]['grow_area_name'] == 'A01'
  assert json[1]['rainfall_thresh_in'] == 1.5
  assert json[1]['geometry'] == [36.303915, -75.864693]

def test_add_invalid_lease(client, dbSession, addMockFbUser):
  # add a mock Firebase user
  addMockFbUser(dict(uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com'), 'validUser1')

  # add the user to the db
  user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com')

  dbSession.add(user)
  dbSession.commit()

  # add one existing lease for the user
  lease = Lease(user_id=user.id, ncdmf_lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5, geometry=(34.404497, -77.567573))

  dbSession.add(lease)
  dbSession.commit()

  # make a request to add the given lease
  res = client.post('/leases', headers={'Authorization': 'validUser1'}, json={'ncdmf_lease_id': '123-CD'})
  assert res.status_code == 400

  # get the user's leases
  res = client.get('/leases', headers={'Authorization': 'validUser1'})
  assert res.status_code == 200

  json = res.get_json()
  assert len(json) == 1
  assert json[0]['ncdmf_lease_id'] == '45678'
  assert json[0]['grow_area_name'] == 'A01'
  assert json[0]['rainfall_thresh_in'] == 1.5
  assert json[0]['geometry'] == [34.404497, -77.567573]
