import pytest

from models.GrowArea import GrowArea
from models.SGAMinMaxProbability import SGAMinMaxProbability

from firebase_admin import auth

NUMBER_OF_GROW_AREAS = 73

def addGrowAreas(dbSession):
  # make sure that grow areas are added to the sgas table
  sgas = []
  for x in range(NUMBER_OF_GROW_AREAS):
    sgas.append(GrowArea(grow_area_name='A' + str(x)))
  dbSession.add_all(sgas)
  dbSession.commit()

def test_valid(client, dbSession):
  # make sure that grow areas are added to the sgas table
  addGrowAreas(dbSession)

  # add some grow area probabilities to the database
  probabilities = [
    SGAMinMaxProbability(grow_area_name='A01', min_1d_prob=40, max_1d_prob=70, min_2d_prob=50, max_2d_prob=80, min_3d_prob=60, max_3d_prob=90),
    SGAMinMaxProbability(grow_area_name='B03', min_1d_prob=40, max_1d_prob=70, min_2d_prob=50, max_2d_prob=80, min_3d_prob=60, max_3d_prob=90),
    SGAMinMaxProbability(grow_area_name='F11', min_1d_prob=40, max_1d_prob=70, min_2d_prob=50, max_2d_prob=80, min_3d_prob=60, max_3d_prob=90)
  ]

  dbSession.add_all(probabilities)
  dbSession.commit()

  res = client.get('/growAreaProbs')
  assert res.status_code == 200

  json = res.get_json()
  assert len(json) == 3

  assert json['A01']['min_1d_prob'] == 40
  assert json['A01']['max_1d_prob'] == 70
  assert json['B03']['min_2d_prob'] == 50
  assert json['B03']['max_2d_prob'] == 80
  assert json['F11']['min_3d_prob'] == 60
  assert json['F11']['max_3d_prob'] == 90

def test_return_all_grow_area_probs(client, dbSession):
  # make sure that grow areas are added to the sgas table
  addGrowAreas(dbSession)

  # add one probability at the beginning
  firstProb = SGAMinMaxProbability(grow_area_name='A00', min_1d_prob=40, max_1d_prob=70, min_2d_prob=50, max_2d_prob=80, min_3d_prob=60, max_3d_prob=90)
  dbSession.add(firstProb)
  dbSession.commit()

  # add a probability for each growing area
  probabilities = []
  for x in range(NUMBER_OF_GROW_AREAS):
    probabilities.append(SGAMinMaxProbability(grow_area_name='B'+str(x), min_1d_prob=x, max_1d_prob=x, min_2d_prob=x, max_2d_prob=x, min_3d_prob=x, max_3d_prob=x))
  dbSession.add_all(probabilities)
  dbSession.commit()

  res = client.get('/growAreaProbs')
  assert res.status_code == 200

  json = res.get_json()
  assert len(json) == NUMBER_OF_GROW_AREAS

  print(list(json))

  for probGrowArea in json:
    assert 'B' in probGrowArea
  
  # add another set of probabilities for each growing area
  probabilities = []
  for x in range(NUMBER_OF_GROW_AREAS):
    y = x + 10
    probabilities.append(SGAMinMaxProbability(grow_area_name='C'+str(y), min_1d_prob=y, max_1d_prob=y, min_2d_prob=y, max_2d_prob=y, min_3d_prob=y, max_3d_prob=y))
  dbSession.add_all(probabilities)
  dbSession.commit()

  res = client.get('/growAreaProbs')
  assert res.status_code == 200

  json = res.get_json()
  assert len(json) == NUMBER_OF_GROW_AREAS

  for probGrowArea in json:
    assert 'C' in probGrowArea
