import pytest

from models.Lease import Lease

def test_Lease(dbSession):
  geoJson = {
    'type': 'Feature',
    'geometry': {
      'type': 'Point',
      'coordinates': [-75.985285, 35.803644] # lon, lat
    }
  }
  validLease1 = Lease(ncdmf_lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5, window_pref=1, prob_pref=50, geo_boundary=geoJson)

  dbSession.add(validLease1)
  dbSession.commit()

  assert validLease1.id == 1

  res = Lease.query.all()

  assert len(res) == 1
  assert res[0].ncdmf_lease_id == validLease1.ncdmf_lease_id
  assert res[0].grow_area_name == validLease1.grow_area_name
  assert res[0].rainfall_thresh_in == validLease1.rainfall_thresh_in
  assert res[0].window_pref == validLease1.window_pref
  assert res[0].prob_pref == validLease1.prob_pref
  assert res[0].geo_boundary == validLease1.geo_boundary

def test_asDict(genRandomString):
  geoJson = {
    'type': 'Feature',
    'geometry': {
      'type': 'Point',
      'coordinates': [-75.985285, 35.803644] # lon, lat
    }
  }
  lease = Lease(ncdmf_lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5, window_pref=1, prob_pref=50, geo_boundary=geoJson)

  dictForm = lease.asDict()

  assert dictForm['ncdmf_lease_id'] == lease.ncdmf_lease_id
  assert dictForm['grow_area_name'] == lease.grow_area_name
  assert dictForm['rainfall_thresh_in'] == lease.rainfall_thresh_in
  assert dictForm['window_pref'] == lease.window_pref
  assert dictForm['prob_pref'] == lease.prob_pref
  assert dictForm['geo_boundary'] == lease.geo_boundary

def test_repr(genRandomString):
  lease = Lease(user_id=9, ncdmf_lease_id='45678', grow_area_name='A01', rainfall_thresh_in=1.5)

  stringForm = lease.__repr__()

  assert 'Lease' in stringForm
  assert str(lease.user_id) in stringForm
  assert lease.ncdmf_lease_id in stringForm
  assert lease.grow_area_name in stringForm
