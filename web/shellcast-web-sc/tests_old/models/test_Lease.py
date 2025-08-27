import pytest

from models.Lease import Lease

def test_Lease(dbSession):
  validLease1 = Lease(lease_id='45678', grow_area_name=None, cmu_name=None, rainfall_thresh_in=1.5, latitude=35.803644, longitude=-75.985285)

  dbSession.add(validLease1)
  dbSession.commit()

  assert validLease1.id == 1

  res = Lease.query.all()

  assert len(res) == 1
  assert res[0].lease_id == validLease1.lease_id
  assert res[0].grow_area_name == validLease1.grow_area_name
  assert res[0].cmu_name == validLease1.cmu_name
  assert res[0].rainfall_thresh_in == validLease1.rainfall_thresh_in
  assert res[0].latitude == validLease1.latitude
  assert res[0].longitude == validLease1.longitude

def test_asDict():
  lease = Lease(lease_id='45678', grow_area_name='A01', cmu_name='U001', rainfall_thresh_in=1.5, latitude=35.803644, longitude=-75.985285)

  dictForm = lease.asDict()

  assert dictForm['lease_id'] == lease.ncdmf_lease_id
  assert dictForm['rainfall_thresh_in'] == lease.rainfall_thresh_in
  assert dictForm['latitude'] == lease.latitude
  assert dictForm['longitude'] == lease.longitude

def test_repr():
  lease = Lease(ncdmf_lease_id='45678', grow_area_name='A01', cmu_name='U001', rainfall_thresh_in=1.5)

  stringForm = lease.__repr__()

  assert 'Lease' in stringForm
  assert lease.lease_id in stringForm
  assert lease.rainfall_thresh_in in stringForm
  assert lease.latitude in stringForm
  assert lease.longitude in stringForm
