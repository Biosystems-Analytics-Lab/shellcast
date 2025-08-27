import pytest

from models.Lease import Lease
from models.CMUProbability import CMUProbability

from firebase_admin import auth

NUMBER_OF_GROWING_UNITS = 149

def addGrowingUnits(dbSession):
  # make sure that growing units are added to the cmus table
  cmus = []
  for x in range(NUMBER_OF_GROWING_UNITS):
    cmus.append(Lease(lease_id='U' + str(x)))
  dbSession.add_all(cmus)
  dbSession.commit()

def test_valid(client, dbSession):
  # make sure that growing units are added to the cmus table
  addGrowingUnits(dbSession)

  # add some growing unit probabilities to the database
  probabilities = [
    CMUProbability(lease_id='A01', prob_1d_perc=40, prob_2d_perc=50, prob_3d_perc=60),
    CMUProbability(lease_id='B03', prob_1d_perc=40, prob_2d_perc=50, prob_3d_perc=60),
    CMUProbability(lease_id='F11', prob_1d_perc=40, prob_2d_perc=50, prob_3d_perc=60),
  ]

  dbSession.add_all(probabilities)
  dbSession.commit()

  res = client.get('/growingUnitProbs')
  assert res.status_code == 200

  json = res.get_json()
  assert len(json) == 3

  assert json['A01']['prob_1d_perc'] == 40
  assert json['B03']['prob_2d_perc'] == 50
  assert json['F11']['prob_3d_perc'] == 60

def test_returnAllGrowingUnitProbs(client, dbSession):
  # make sure that growing units are added to the cmus table
  addGrowingUnits(dbSession)

  # add one probability at the beginning
  firstProb = CMUProbability(lease_id='A00', prob_1d_perc=40, prob_2d_perc=50, prob_3d_perc=60)
  dbSession.add(firstProb)
  dbSession.commit()

  # add a probability for each growing unit
  probabilities = []
  for x in range(NUMBER_OF_GROWING_UNITS):
    probabilities.append(CMUProbability(lease_id='B'+str(x), prob_1d_perc=x, prob_2d_perc=x, prob_3d_perc=x))
  dbSession.add_all(probabilities)
  dbSession.commit()

  res = client.get('/growingUnitProbs')
  assert res.status_code == 200

  json = res.get_json()
  assert len(json) == NUMBER_OF_GROWING_UNITS

  print(list(json))

  for cmuName in json:
    assert 'B' in cmuName
  
  # add another set of probabilities for each growing unit
  probabilities = []
  for x in range(NUMBER_OF_GROWING_UNITS):
    y = x + 10
    probabilities.append(CMUProbability(lease_id='C'+str(y), prob_1d_perc=y, prob_2d_perc=y, prob_3d_perc=y))
  dbSession.add_all(probabilities)
  dbSession.commit()

  res = client.get('/growingUnitProbs')
  assert res.status_code == 200

  json = res.get_json()
  assert len(json) == NUMBER_OF_GROWING_UNITS

  for cmuName in json:
    assert 'C' in cmuName
