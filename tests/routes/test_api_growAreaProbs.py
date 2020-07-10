import pytest

from models.SGAMinMaxProbability import SGAMinMaxProbability

from firebase_admin import auth

def test_valid(client, dbSession):
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

def test_73(client, dbSession):
  # add one probability at the beginning
  firstProb = SGAMinMaxProbability(grow_area_name='A00', min_1d_prob=40, max_1d_prob=70, min_2d_prob=50, max_2d_prob=80, min_3d_prob=60, max_3d_prob=90)
  dbSession.add(firstProb)
  dbSession.commit()

  # add a probability for each growing area
  probabilities = []
  for x in range(73):
    probabilities.append(SGAMinMaxProbability(grow_area_name='B'+str(x), min_1d_prob=x, max_1d_prob=x, min_2d_prob=x, max_2d_prob=x, min_3d_prob=x, max_3d_prob=x))
  dbSession.add_all(probabilities)
  dbSession.commit()

  res = client.get('/growAreaProbs')
  assert res.status_code == 200

  json = res.get_json()
  assert len(json) == 73

  print(list(json))

  for probGrowArea in json:
    assert 'B' in probGrowArea
  
  # add another set of probabilities for each growing area
  probabilities = []
  for x in range(73):
    y = x + 10
    probabilities.append(SGAMinMaxProbability(grow_area_name='C'+str(y), min_1d_prob=y, max_1d_prob=y, min_2d_prob=y, max_2d_prob=y, min_3d_prob=y, max_3d_prob=y))
  dbSession.add_all(probabilities)
  dbSession.commit()

  res = client.get('/growAreaProbs')
  assert res.status_code == 200

  json = res.get_json()
  assert len(json) == 73

  for probGrowArea in json:
    assert 'C' in probGrowArea
