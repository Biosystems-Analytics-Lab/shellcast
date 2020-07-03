import pytest

from models.User import User
from models.Lease import Lease
from models.ClosureProbability import ClosureProbability

from firebase_admin import auth

def test_valid(client, dbSession, addMockFbUser):
  # add a mock Firebase user
  addMockFbUser(dict(uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com', phone_number='11234567890'), 'validUser1')

  # add the user to the db
  user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com', phone_number='11234567890')

  dbSession.add(user)
  dbSession.commit()

  # add some leases to the database
  leases = [
    Lease(user_id=user.id, ncdmf_lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5, geo_boundary='{"type": "Feature", "geometry": {"type": "Point", "coordinates": [-77.567573, 34.404497]}}'),
    Lease(user_id=user.id, ncdmf_lease_id='12345', grow_area_name='B02', rainfall_thresh_in=2.5, geo_boundary='{"type": "Feature", "geometry": {"type": "Point", "coordinates": [-76.523872, 35.207332]}}'),
    Lease(user_id=user.id, ncdmf_lease_id='82945', grow_area_name='C01', rainfall_thresh_in=1.5, geo_boundary='{"type": "Feature", "geometry": {"type": "Point", "coordinates": [-75.927864, 36.164344]}}')
  ]

  dbSession.add_all(leases)
  dbSession.commit()

  # add some closure probabilities to the database
  probabilities = [
    ClosureProbability(lease_id=leases[0].id, prob_1d_perc=60, prob_2d_perc=70, prob_3d_perc=80),
    ClosureProbability(lease_id=leases[1].id, prob_1d_perc=45, prob_2d_perc=54, prob_3d_perc=57),
    ClosureProbability(lease_id=leases[2].id, prob_1d_perc=32, prob_2d_perc=33, prob_3d_perc=69)
  ]

  dbSession.add_all(probabilities)
  dbSession.commit()

  res = client.get('/leaseProbs', headers={'Authorization': 'validUser1'})
  assert res.status_code == 200

  json = res.get_json()
  assert len(json) == 3

  assert json[0]['prob_1d_perc'] == 60
  assert json[0]['prob_2d_perc'] == 70
  assert json[0]['prob_3d_perc'] == 80
  assert json[0]['ncdmf_lease_id'] == '45678'
  assert json[0]['geo_boundary'] == '{"type": "Feature", "geometry": {"type": "Point", "coordinates": [-77.567573, 34.404497]}}'
  assert json[1]['prob_1d_perc'] == 45
  assert json[1]['prob_2d_perc'] == 54
  assert json[1]['prob_3d_perc'] == 57
  assert json[1]['ncdmf_lease_id'] == '12345'
  assert json[1]['geo_boundary'] == '{"type": "Feature", "geometry": {"type": "Point", "coordinates": [-76.523872, 35.207332]}}'
  assert json[2]['prob_1d_perc'] == 32
  assert json[2]['prob_2d_perc'] == 33
  assert json[2]['prob_3d_perc'] == 69
  assert json[2]['ncdmf_lease_id'] == '82945'
  assert json[2]['geo_boundary'] == '{"type": "Feature", "geometry": {"type": "Point", "coordinates": [-75.927864, 36.164344]}}'
