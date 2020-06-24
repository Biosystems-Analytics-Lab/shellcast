from flask import Blueprint, jsonify, request

from models import db
from models.User import User
from models.ClosureProbability import ClosureProbability
from models.SGAMinMaxProbability import SGAMinMaxProbability
from models.Lease import Lease

# import time

from routes.authentication import userRequired

api = Blueprint('api', __name__)

@api.route('/userInfo')
@userRequired
def getUserInfo(user):
  return user.asDict()

def queryLeaseClosureProbabilities(user):
  leases = db.session.query(Lease).filter_by(user_id=user.id).all()
  probs = []
  for lease in leases:
    closureProb = db.session.query(ClosureProbability).filter_by(lease_id=lease.id).first()
    probDict = closureProb.asDict()
    probDict['ncdmf_lease_id'] = lease.ncdmf_lease_id
    probs.append(closureProb.asDict())
  return probs

@api.route('/leaseProbs')
@userRequired
def getLeaseClosureProbabilities(user):
  return jsonify(queryLeaseClosureProbabilities(user))

def queryGrowAreaProbabilities():
  results = db.session.query(SGAMinMaxProbability).all()
  dictOfCPs = {}
  for r in results:
    sgaName = r.grow_area_name
    dictOfCPs[sgaName] = r.asDict()
  return dictOfCPs

@api.route('/growAreaProbs')
def getAreaData():
  # t0 = time.perf_counter_ns()
  dictOfCPs = queryGrowAreaProbabilities()
  # t1 = time.perf_counter_ns()
  # print('Total query time: {} ms'.format((t1 - t0) / 1000000))

  return jsonify(dictOfCPs)
