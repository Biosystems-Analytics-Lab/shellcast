from flask import Blueprint, jsonify
from models import db
from models.ClosureProbability import ClosureProbability
from models.LeaseInfo import LeaseInfo

import time

areaData = Blueprint('areaData', __name__)

def queryClosureProbabilities():
  results = db.session.query(ClosureProbability, LeaseInfo.grow_area_name).join(LeaseInfo).all()
  dictOfCPs = {}
  for r in results:
    sgaName = r[1]
    dictOfCPs[sgaName] = r[0].to_dict()
  return dictOfCPs

@areaData.route('/areaData')
def getAreaData():
  # t0 = time.perf_counter_ns()
  dictOfCPs = queryClosureProbabilities()
  # t1 = time.perf_counter_ns()
  # print('Total query time: {} ms'.format((t1 - t0) / 1000000))

  return jsonify(dictOfCPs)
