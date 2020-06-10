import pytest

from models.LeaseInfo import LeaseInfo

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
