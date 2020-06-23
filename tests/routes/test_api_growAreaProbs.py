import pytest

from models.SGAMinMaxProbability import SGAMinMaxProbability

from firebase_admin import auth

def test_valid(client, dbSession, addMockFbUser):
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
