import pytest

from models.User import User
from models.UserLease import UserLease
from models.NCDMFLease import NCDMFLease

from firebase_admin import auth

def test_search_leases(client, dbSession, addMockFbUser):
  # add a mock Firebase user
  addMockFbUser(dict(uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com'), 'validUser1')

  # add some NCDMF leases
  ncdmfLeases = [
    NCDMFLease(ncdmf_lease_id='819401', grow_area_name='D11', cmu_name='U001', rainfall_thresh_in=2.5, geometry=(34.404497, -77.567573)),
    NCDMFLease(ncdmf_lease_id='123456', grow_area_name='B05', cmu_name='U002', rainfall_thresh_in=3.5, geometry=(35.923741, -76.239482)),
    NCDMFLease(ncdmf_lease_id='4-C-89', grow_area_name='A01', cmu_name='U003', rainfall_thresh_in=1.5, geometry=(36.303915, -75.864693))
  ]
  dbSession.add_all(ncdmfLeases)
  dbSession.commit()

  res = client.post('/searchLeases', headers={'Authorization': 'validUser1'}, json={'search': '1'})
  assert res.status_code == 200

  json = res.get_json()
  assert len(json) == 2

  assert json[0] == '819401'
  assert json[1] == '123456'

def test_search_leases_with_existing_user_lease(client, dbSession, addMockFbUser):
  # add a mock Firebase user
  addMockFbUser(dict(uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com'), 'validUser1')

  # add the user to the db
  user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com')
  dbSession.add(user)
  dbSession.commit()

  # add some NCDMF leases
  ncdmfLeases = [
    NCDMFLease(ncdmf_lease_id='819401', grow_area_name='D11', cmu_name='U001', rainfall_thresh_in=2.5, geometry=(34.404497, -77.567573)),
    NCDMFLease(ncdmf_lease_id='123456', grow_area_name='B05', cmu_name='U002', rainfall_thresh_in=3.5, geometry=(35.923741, -76.239482)),
    NCDMFLease(ncdmf_lease_id='4-C-89', grow_area_name='A01', cmu_name='U003', rainfall_thresh_in=1.5, geometry=(36.303915, -75.864693))
  ]
  dbSession.add_all(ncdmfLeases)
  dbSession.commit()

  # add one existing lease for the user
  lease = UserLease(user_id=user.id, ncdmf_lease_id='123456', grow_area_name='B05', cmu_name='U002', rainfall_thresh_in=3.5, geometry=(35.923741, -76.239482))
  dbSession.add(lease)
  dbSession.commit()

  res = client.post('/searchLeases', headers={'Authorization': 'validUser1'}, json={'search': '1'})
  assert res.status_code == 200

  json = res.get_json()
  assert len(json) == 1

  assert json[0] == '819401'
