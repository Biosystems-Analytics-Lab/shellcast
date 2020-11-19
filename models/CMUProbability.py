from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import functions
from sqlalchemy.orm import relationship

from models import db

class CMUProbability(db.Model):
  __tablename__ = 'cmu_probabilities'
  id = Column(Integer, primary_key=True)
  cmu_name = Column(String(10), nullable=False)
  prob_1d_perc = Column(Integer)
  prob_2d_perc = Column(Integer)
  prob_3d_perc = Column(Integer)
  created = Column(DateTime, server_default=functions.now())
  updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

  def asDict(self):
    return {
      'cmu_name': self.cmu_name,
      'prob_1d_perc': self.prob_1d_perc,
      'prob_2d_perc': self.prob_2d_perc,
      'prob_3d_perc': self.prob_3d_perc
    }

  def __repr__(self):
    return '<CMUProbability: {}, {}, {}, {}>'.format(self.cmu_name, self.prob_1d_perc, self.prob_2d_perc, self.prob_3d_perc)
