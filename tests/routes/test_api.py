import pytest

from models.Lease import Lease
from models.ClosureProbability import ClosureProbability

from firebase_admin import auth

def test_newUser(client, dbSession):
  # I have no way of generating a JWT in this test, so I can only
  # test the case when an invalid JWT is sent to the endpoint.
  res = client.post('/newUser', headers={'Authorization': 'notAValidJWT'})
  assert res.status_code == 401
  assert res.get_json()['message'] == 'ID token is invalid'

def test_areaData(client, dbSession):
  # add some leases to the database
  leases = [
    Lease(ncdmf_lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5),
    Lease(ncdmf_lease_id='12345', grow_area_name='B02', rainfall_thresh_in=2.5),
    Lease(ncdmf_lease_id='82945', grow_area_name='C01', rainfall_thresh_in=1.5),
    Lease(ncdmf_lease_id='74929', grow_area_name='F02', rainfall_thresh_in=2.5),
    Lease(ncdmf_lease_id='96854', grow_area_name='F03', rainfall_thresh_in=0.5),
  ]

  dbSession.add_all(leases)
  dbSession.commit()

  # add some closure probabilities to the database
  probabilities = [
    ClosureProbability(lease_id=leases[0].id, prob_1d_perc=60),
    ClosureProbability(lease_id=leases[1].id, prob_1d_perc=45),
    ClosureProbability(lease_id=leases[2].id, prob_1d_perc=32),
    ClosureProbability(lease_id=leases[3].id, prob_1d_perc=97),
    ClosureProbability(lease_id=leases[4].id, prob_1d_perc=22),
  ]

  dbSession.add_all(probabilities)
  dbSession.commit()

  res = client.get('/areaData')
  assert res.status_code == 200

  json = res.get_json()
  assert len(json) == 5

  assert json['A01']['prob1Day'] == 60
  assert json['B02']['prob1Day'] == 45
  assert json['C01']['prob1Day'] == 32
  assert json['F02']['prob1Day'] == 97
  assert json['F03']['prob1Day'] == 22
