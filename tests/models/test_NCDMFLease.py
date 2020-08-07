import pytest

from models.NCDMFLease import NCDMFLease

def test_NCDMFLease(dbSession):
  validLease1 = NCDMFLease(ncdmf_lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5, geometry=(35.803644, -75.985285))

  dbSession.add(validLease1)
  dbSession.commit()

  assert validLease1.id == 1

  res = NCDMFLease.query.all()

  assert len(res) == 1
  assert res[0].ncdmf_lease_id == validLease1.ncdmf_lease_id
  assert res[0].grow_area_name == validLease1.grow_area_name
  assert res[0].rainfall_thresh_in == validLease1.rainfall_thresh_in
  assert res[0].geometry == validLease1.geometry

def test_asDict():
  lease = NCDMFLease(ncdmf_lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5, geometry=(35.803644, -75.985285))

  dictForm = lease.asDict()

  assert dictForm['ncdmf_lease_id'] == lease.ncdmf_lease_id
  assert dictForm['grow_area_name'] == lease.grow_area_name
  assert dictForm['rainfall_thresh_in'] == lease.rainfall_thresh_in
  assert dictForm['geometry'] == lease.geometry

def test_repr():
  lease = NCDMFLease(ncdmf_lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5)

  stringForm = lease.__repr__()

  assert 'NCDMFLease' in stringForm
  assert lease.ncdmf_lease_id in stringForm
  assert lease.grow_area_name in stringForm
