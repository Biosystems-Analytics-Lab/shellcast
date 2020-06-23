import pytest

from models.SGAMinMaxProbability import SGAMinMaxProbability

def test_valid(dbSession):
  sga = SGAMinMaxProbability(grow_area_name='A01', min_1d_prob=12, max_1d_prob=30, min_2d_prob=6, max_2d_prob=54, min_3d_prob=33, max_3d_prob=87)

  dbSession.add(sga)
  dbSession.commit()

  assert sga.id == 1

  res = SGAMinMaxProbability.query.all()

  assert len(res) == 1
  assert res[0].grow_area_name == sga.grow_area_name
  assert res[0].min_1d_prob == sga.min_1d_prob
  assert res[0].max_1d_prob == sga.max_1d_prob
  assert res[0].min_2d_prob == sga.min_2d_prob
  assert res[0].max_2d_prob == sga.max_2d_prob
  assert res[0].min_3d_prob == sga.min_3d_prob
  assert res[0].max_3d_prob == sga.max_3d_prob

def test_asDict():
  sga = SGAMinMaxProbability(grow_area_name='A01', min_1d_prob=12, max_1d_prob=30, min_2d_prob=6, max_2d_prob=54, min_3d_prob=33, max_3d_prob=87)

  dictForm = sga.asDict()

  assert dictForm.get('grow_area_name') == None
  assert dictForm['min_1d_prob'] == sga.min_1d_prob
  assert dictForm['max_1d_prob'] == sga.max_1d_prob
  assert dictForm['min_2d_prob'] == sga.min_2d_prob
  assert dictForm['max_2d_prob'] == sga.max_2d_prob
  assert dictForm['min_3d_prob'] == sga.min_3d_prob
  assert dictForm['max_3d_prob'] == sga.max_3d_prob

def test_repr():
  sga = SGAMinMaxProbability(grow_area_name='A01', min_1d_prob=12, max_1d_prob=30, min_2d_prob=6, max_2d_prob=54, min_3d_prob=33, max_3d_prob=87)

  stringForm = sga.__repr__()

  assert 'SGAMinMax' in stringForm
  assert sga.grow_area_name in stringForm
