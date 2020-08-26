import pytest

from models.GrowArea import GrowArea

def test_valid(dbSession, genRandomString):
  validArea1 = GrowArea(grow_area_name='A01')

  dbSession.add(validArea1)
  dbSession.commit()

  assert validArea1.id == 1

  res = GrowArea.query.all()

  assert len(res) == 1
  assert res[0].grow_area_name == validArea1.grow_area_name
  assert res[0].geometry == None

  additionalAreas = [
    GrowArea(grow_area_name='C01'),
    GrowArea(grow_area_name='E23'),
    GrowArea(grow_area_name='B04')
  ]

  dbSession.add_all(additionalAreas)
  dbSession.commit()

  assert additionalAreas[0].id == 2
  assert additionalAreas[1].id == 3
  assert additionalAreas[2].id == 4

  res = GrowArea.query.all()

  assert len(res) == len(additionalAreas) + 1

def test_asDict(genRandomString):
  area = GrowArea(grow_area_name='C01')

  dictForm = area.asDict()

  assert dictForm['grow_area_name'] == area.grow_area_name
  assert dictForm['geometry'] == None

def test_repr(genRandomString):
  area = GrowArea(grow_area_name='C01')

  stringForm = area.__repr__()

  assert 'GrowArea' in stringForm
  assert area.grow_area_name in stringForm
