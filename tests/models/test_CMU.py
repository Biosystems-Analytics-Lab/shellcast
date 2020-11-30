import pytest

from models.CMU import CMU

def test_valid(dbSession, genRandomString):
  validUnit1 = CMU(cmu_name='U001')

  dbSession.add(validUnit1)
  dbSession.commit()

  assert validUnit1.id == 1

  res = CMU.query.all()

  assert len(res) == 1
  assert res[0].cmu_name == validUnit1.cmu_name

  additionalUnits = [
    CMU(cmu_name='U023'),
    CMU(cmu_name='U004'),
    CMU(cmu_name='U128')
  ]

  dbSession.add_all(additionalUnits)
  dbSession.commit()

  assert additionalUnits[0].id == 2
  assert additionalUnits[1].id == 3
  assert additionalUnits[2].id == 4

  res = CMU.query.all()

  assert len(res) == len(additionalUnits) + 1

def test_asDict(genRandomString):
  unit = CMU(cmu_name='U001')

  dictForm = unit.asDict()

  assert dictForm['cmu_name'] == unit.cmu_name

def test_repr(genRandomString):
  unit = CMU(cmu_name='U007')

  stringForm = unit.__repr__()

  assert 'CMU' in stringForm
  assert unit.cmu_name in stringForm
