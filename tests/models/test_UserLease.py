import pytest

from models.User import User
from models.UserLease import UserLease
from models.CMUProbability import CMUProbability

def test_valid(dbSession):
  # add the user to the db
  user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com')
  dbSession.add(user)
  dbSession.commit()

  validLease1 = UserLease(user_id=user.id, ncdmf_lease_id='45678', grow_area_name='A01', cmu_name='U001', rainfall_thresh_in=1.5, geometry=(35.803644, -75.985285))

  dbSession.add(validLease1)
  dbSession.commit()

  assert validLease1.id == 1

  res = UserLease.query.all()

  assert len(res) == 1
  assert res[0].ncdmf_lease_id == validLease1.ncdmf_lease_id
  assert res[0].grow_area_name == validLease1.grow_area_name
  assert res[0].cmu_name == validLease1.cmu_name
  assert res[0].rainfall_thresh_in == validLease1.rainfall_thresh_in
  assert res[0].geometry == validLease1.geometry
  # do some checks to make sure that these are no longer stored by UserLease
  assert not hasattr(res[0], 'email_pref')
  assert not hasattr(res[0], 'text_pref')
  assert not hasattr(res[0], 'prob_pref')

def test_getLatestProbability(dbSession):
  # add a user and a lease to the db
  user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com')
  dbSession.add(user)
  dbSession.commit()
  lease = UserLease(user_id=user.id, ncdmf_lease_id='45678', grow_area_name='A01', cmu_name='U001', rainfall_thresh_in=1.5, geometry=(35.803644, -75.985285))
  dbSession.add(lease)
  dbSession.commit()

  # add a few probabilities for various CMUs
  probs = [
    CMUProbability(cmu_name='U001', prob_1d_perc=60),
    CMUProbability(cmu_name='U002', prob_1d_perc=70),
    CMUProbability(cmu_name='U003', prob_1d_perc=80),
    CMUProbability(cmu_name='U004', prob_1d_perc=90),
  ]
  dbSession.add_all(probs)
  dbSession.commit()

  # add more recent probabilities for the CMUs
  probs = [
    CMUProbability(cmu_name='U001', prob_1d_perc=1),
    CMUProbability(cmu_name='U002', prob_1d_perc=2),
    CMUProbability(cmu_name='U003', prob_1d_perc=3),
    CMUProbability(cmu_name='U004', prob_1d_perc=4),
  ]
  dbSession.add_all(probs)
  dbSession.commit()

  assert lease.getLatestProbability().prob_1d_perc == 1

def test_asDict():
  lease = UserLease(ncdmf_lease_id='45678', grow_area_name='A01', cmu_name='U001', rainfall_thresh_in=1.5, geometry=(35.803644, -75.985285))

  dictForm = lease.asDict()

  assert dictForm['ncdmf_lease_id'] == lease.ncdmf_lease_id
  assert dictForm['grow_area_name'] == lease.grow_area_name
  assert dictForm['cmu_name'] == lease.cmu_name
  assert dictForm['rainfall_thresh_in'] == lease.rainfall_thresh_in
  assert dictForm['geometry'] == lease.geometry
  # do some checks to make sure that these are no longer stored by UserLease
  assert dictForm.get('email_pref') == None
  assert dictForm.get('text_pref') == None
  assert dictForm.get('prob_pref') == None

def test_repr():
  lease = UserLease(user_id=9, ncdmf_lease_id='45678', grow_area_name='A01', cmu_name='U001', rainfall_thresh_in=1.5)

  stringForm = lease.__repr__()

  assert 'UserLease' in stringForm
  assert str(lease.user_id) in stringForm
  assert lease.ncdmf_lease_id in stringForm
  assert lease.grow_area_name in stringForm
  assert lease.cmu_name in stringForm
