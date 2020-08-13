from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import functions
from sqlalchemy.orm import relationship

from models import db
from models.Notification import Notification

class ClosureProbability(db.Model):
  __tablename__ = 'closure_probabilities'
  id = Column(Integer, primary_key=True)
  lease_id = Column(Integer, ForeignKey('user_leases.id'))
  prob_1d_perc = Column(Integer)
  prob_2d_perc = Column(Integer)
  prob_3d_perc = Column(Integer)
  created = Column(DateTime, server_default=functions.now())
  updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

  lease = relationship('Lease', back_populates='closureProbabilities')

  def asDict(self):
    return {
      'prob_1d_perc': self.prob_1d_perc,
      'prob_2d_perc': self.prob_2d_perc,
      'prob_3d_perc': self.prob_3d_perc
    }

  def __repr__(self):
    return '<ClosureProbability({}, {}, {}, {})>'.format(self.lease_id, self.prob_1d_perc, self.prob_2d_perc, self.prob_3d_perc)
