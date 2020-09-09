import pytest

from models.User import User
from models.Lease import Lease

def test_Lease(dbSession):
  # add the user to the db
  user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com')
  dbSession.add(user)
  dbSession.commit()

  validLease1 = Lease(user_id=user.id, ncdmf_lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5, prob_pref=50, geometry=(35.803644, -75.985285))

  dbSession.add(validLease1)
  dbSession.commit()

  assert validLease1.id == 1

  res = Lease.query.all()

  assert len(res) == 1
  assert res[0].ncdmf_lease_id == validLease1.ncdmf_lease_id
  assert res[0].grow_area_name == validLease1.grow_area_name
  assert res[0].rainfall_thresh_in == validLease1.rainfall_thresh_in
  assert res[0].email_pref == False
  assert res[0].text_pref == False
  assert res[0].prob_pref == validLease1.prob_pref
  assert res[0].geometry == validLease1.geometry

def test_asDict():
  lease = Lease(ncdmf_lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5, email_pref=True, text_pref=True, prob_pref=50, geometry=(35.803644, -75.985285))

  dictForm = lease.asDict()

  assert dictForm['ncdmf_lease_id'] == lease.ncdmf_lease_id
  assert dictForm['grow_area_name'] == lease.grow_area_name
  assert dictForm['rainfall_thresh_in'] == lease.rainfall_thresh_in
  assert dictForm['email_pref'] == lease.email_pref
  assert dictForm['text_pref'] == lease.text_pref
  assert dictForm['prob_pref'] == lease.prob_pref
  assert dictForm['geometry'] == lease.geometry

def test_repr():
  lease = Lease(user_id=9, ncdmf_lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5)

  stringForm = lease.__repr__()

  assert 'Lease' in stringForm
  assert str(lease.user_id) in stringForm
  assert lease.ncdmf_lease_id in stringForm
  assert lease.grow_area_name in stringForm
