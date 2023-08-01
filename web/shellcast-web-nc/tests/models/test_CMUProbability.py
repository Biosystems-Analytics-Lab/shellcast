import pytest

from models.CMUProbability import CMUProbability

def test_valid(dbSession):
  # add some probabilities to the database
  probs = [
    CMUProbability(cmu_name='U001', prob_1d_perc=60),
    CMUProbability(cmu_name='U002', prob_1d_perc=70),
    CMUProbability(cmu_name='U003', prob_1d_perc=80),
    CMUProbability(cmu_name='U004', prob_1d_perc=90),
  ]

  dbSession.add_all(probs)
  dbSession.commit()

  assert probs[0].id == 1
  assert probs[1].id == 2
  assert probs[2].id == 3
  assert probs[3].id == 4

  res = CMUProbability.query.all()

  assert len(res) == len(probs)
  assert res[0].cmu_name == probs[0].cmu_name
  assert res[1].cmu_name == probs[1].cmu_name
  assert res[2].cmu_name == probs[2].cmu_name
  assert res[3].cmu_name == probs[3].cmu_name

def test_asDict():
  prob = CMUProbability(cmu_name='U004', prob_1d_perc=60, prob_2d_perc=70, prob_3d_perc=80)

  dictForm = prob.asDict()

  assert dictForm['cmu_name'] == prob.cmu_name  
  assert dictForm['prob_1d_perc'] == prob.prob_1d_perc
  assert dictForm['prob_2d_perc'] == prob.prob_2d_perc
  assert dictForm['prob_3d_perc'] == prob.prob_3d_perc

def test_repr():
  prob = CMUProbability(cmu_name='U004', prob_1d_perc=60, prob_2d_perc=70, prob_3d_perc=80)

  stringForm = prob.__repr__()

  assert 'CMUProbability' in stringForm
  assert str(prob.cmu_name) in stringForm
  assert str(prob.prob_1d_perc) in stringForm
  assert str(prob.prob_2d_perc) in stringForm
  assert str(prob.prob_3d_perc) in stringForm
