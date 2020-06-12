from flask import Blueprint, jsonify, request

from models import db
from models.User import User
from models.ClosureProbability import ClosureProbability
from models.Lease import Lease

import time

from routes.authentication import userRequired

api = Blueprint('api', __name__)

@api.route('/userInfo')
@userRequired
def getUserInfo(user):
  return user.asDict()

def queryClosureProbabilities():
  results = db.session.query(ClosureProbability, Lease.grow_area_name).join(Lease).all()
  dictOfCPs = {}
  for r in results:
    sgaName = r[1]
    dictOfCPs[sgaName] = r[0].asDict()
  return dictOfCPs

@api.route('/areaData')
def getAreaData():
  # t0 = time.perf_counter_ns()
  dictOfCPs = queryClosureProbabilities()
  # t1 = time.perf_counter_ns()
  # print('Total query time: {} ms'.format((t1 - t0) / 1000000))

  return jsonify(dictOfCPs)
