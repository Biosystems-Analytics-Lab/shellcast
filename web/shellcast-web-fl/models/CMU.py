import json
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import functions
from sqlalchemy.orm import relationship

from models import db

class CMU(db.Model):
  __tablename__ = 'cmus'

  id = Column(String(10), primary_key=True)
  sh_name = Column(String(50), nullable=False)
  rainfall_desc = Column(String(100))
  rainfall_thresh_days = Column(Integer)
  rainfall_thresh_in = Column(Float)
  emerg_cond = Column(String(3))
  created = Column(DateTime, server_default=functions.now())

  cmu_probabilities = relationship('CMUProbability', back_populates='cmus')
  leases = relationship('Lease', back_populates='cmus')
  # updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())
  def asDict(self):
    return {
      'id': self.id,
      'sh_name': self.sh_name,
      'rainfall_desc': self.rainfall_desc.replace('\"', '"'),
      'rainfall_thresh_days': self.rainfall_thresh_days,
      'rainfall_thresh_in': self.rainfall_thresh_in,
      'emerg_cond': self.emerg_cond
    }

  def __repr__(self):
      return ('<CMU: '
              f'{self.id}, {self.sh_name}, {self.rainfall_desc}, '
              f'{self.rainfall_thresh_days}, {self.rainfall_thresh_in}, '
              f'{self.emerg_cond}>')

