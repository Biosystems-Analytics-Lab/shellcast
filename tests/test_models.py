import pytest

from models.User import User
from models.LeaseInfo import LeaseInfo
from models.ClosureProbability import ClosureProbability

def test_User(dbSession):
  validUser1 = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='asdf@adf.com', phone_number='11234567890', first_name='as', last_name='df')

  dbSession.add(validUser1)
  dbSession.commit()

  assert validUser1.id == 1

  res = User.query.all()

  assert len(res) == 1
  assert res[0].firebase_uid == validUser1.firebase_uid

def test_LeaseInfo(dbSession):
  geoJson = {
    'type': 'Feature',
    'geometry': {
      'type': 'Point',
      'coordinates': [-75.985285, 35.803644] # lon, lat
    }
  }
  validLease1 = LeaseInfo(lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5, geo_boundary=geoJson)

  dbSession.add(validLease1)
  dbSession.commit()

  assert validLease1.id == 1

  res = LeaseInfo.query.all()

  assert len(res) == 1
  assert res[0].lease_id == validLease1.lease_id

def test_ClosureProbability(dbSession):
  # add some leases to the database
  leases = [
    LeaseInfo(lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5),
    LeaseInfo(lease_id='12345', grow_area_name='B02', rainfall_thresh_in=2.5),
    LeaseInfo(lease_id='82945', grow_area_name='C01', rainfall_thresh_in=1.5),
    LeaseInfo(lease_id='74929', grow_area_name='F02', rainfall_thresh_in=2.5),
    LeaseInfo(lease_id='96854', grow_area_name='F03', rainfall_thresh_in=0.5),
  ]

  dbSession.add_all(leases)
  dbSession.commit()

  # add some closure probabilities to the database
  probs = [
    ClosureProbability(lease_info_id=leases[0].id, prob_1d_perc=60),
    ClosureProbability(lease_info_id=leases[1].id, prob_1d_perc=45),
    ClosureProbability(lease_info_id=leases[2].id, prob_1d_perc=32),
    ClosureProbability(lease_info_id=leases[3].id, prob_1d_perc=97),
    ClosureProbability(lease_info_id=leases[4].id, prob_1d_perc=22),
  ]

  dbSession.add_all(probs)
  dbSession.commit()

  assert probs[0].id == 1
  assert probs[1].id == 2
  assert probs[2].id == 3
  assert probs[3].id == 4
  assert probs[4].id == 5

  res = ClosureProbability.query.all()

  assert len(res) == len(probs)
  assert res[0].lease_info_id == probs[0].lease_info_id
  assert res[1].lease_info_id == probs[1].lease_info_id
  assert res[2].lease_info_id == probs[2].lease_info_id
  assert res[3].lease_info_id == probs[3].lease_info_id
  assert res[4].lease_info_id == probs[4].lease_info_id
