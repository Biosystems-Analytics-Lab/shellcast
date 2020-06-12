import pytest

from models.Lease import Lease
from models.ClosureProbability import ClosureProbability

def test_valid(dbSession):
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
  probs = [
    ClosureProbability(lease_id=leases[0].id, prob_1d_perc=60),
    ClosureProbability(lease_id=leases[1].id, prob_1d_perc=45),
    ClosureProbability(lease_id=leases[2].id, prob_1d_perc=32),
    ClosureProbability(lease_id=leases[3].id, prob_1d_perc=97),
    ClosureProbability(lease_id=leases[4].id, prob_1d_perc=22),
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
  assert res[0].lease_id == probs[0].lease_id
  assert res[1].lease_id == probs[1].lease_id
  assert res[2].lease_id == probs[2].lease_id
  assert res[3].lease_id == probs[3].lease_id
  assert res[4].lease_id == probs[4].lease_id

def test_asDict():
  prob = ClosureProbability(lease_id=1, rain_forecast_1d_in=2, rain_forecast_2d_in=3.2, rain_forecast_3d_in=4.5, prob_1d_perc=60, prob_2d_perc=70, prob_3d_perc=80)

  dictForm = prob.asDict()

  assert dictForm['rain_forecast_1d_in'] == prob.rain_forecast_1d_in
  assert dictForm['rain_forecast_2d_in'] == prob.rain_forecast_2d_in
  assert dictForm['rain_forecast_3d_in'] == prob.rain_forecast_3d_in
  assert dictForm['prob_1d_perc'] == prob.prob_1d_perc
  assert dictForm['prob_2d_perc'] == prob.prob_2d_perc
  assert dictForm['prob_3d_perc'] == prob.prob_3d_perc

def test_repr():
  prob = ClosureProbability(lease_id=1, rain_forecast_1d_in=2, rain_forecast_2d_in=3.2, rain_forecast_3d_in=4.5, prob_1d_perc=60, prob_2d_perc=70, prob_3d_perc=80)

  stringForm = prob.__repr__()

  assert 'ClosureProbability' in stringForm
  assert str(prob.lease_id) in stringForm
  assert str(prob.prob_1d_perc) in stringForm
  assert str(prob.prob_2d_perc) in stringForm
  assert str(prob.prob_3d_perc) in stringForm
