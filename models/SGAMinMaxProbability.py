from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import functions

from models import db

class SGAMinMaxProbability(db.Model):
  __tablename__ = 'sga_min_max'

  id = Column(Integer, primary_key=True)
  grow_area_name = Column(String(3))
  min_1d_prob = Column(Integer)
  max_1d_prob = Column(Integer)
  min_2d_prob = Column(Integer)
  max_2d_prob = Column(Integer)
  min_3d_prob = Column(Integer)
  max_3d_prob = Column(Integer)
  created = Column(DateTime, server_default=functions.now())
  updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

  def asDict(self):
    return {
      'min_1d_prob': self.min_1d_prob,
      'max_1d_prob': self.max_1d_prob,
      'min_2d_prob': self.min_2d_prob,
      'max_2d_prob': self.max_2d_prob,
      'min_3d_prob': self.min_3d_prob,
      'max_3d_prob': self.max_3d_prob,
    }

  def __repr__(self):
    return '<SGAMinMax: {}>'.format(self.grow_area_name)
