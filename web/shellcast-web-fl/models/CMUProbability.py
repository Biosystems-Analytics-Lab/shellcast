from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import functions
from models import db
from models.CMU import CMU  # DO NOT REMOVE THIS IMPORT


class CMUProbability(db.Model):
  __tablename__ = 'cmu_probabilities'

  id = Column(Integer, primary_key=True)
  cmu_name = Column(String(10), ForeignKey('cmus.id'), nullable=False)
  prob_1d_perc = Column(Integer)
  created = Column(DateTime, server_default=functions.now())

  cmus = db.relationship('CMU')

  def asDict(self):
    return {
      'cmu_name': self.cmu_name,
      'sh_name': self.cmus.sh_name,
      'prob_1d_perc': self.prob_1d_perc,
    }

  def __repr__(self):
    return '<CMUProbability: {}, {}>'.format(self.cmu_name, self.prob_1d_perc)
