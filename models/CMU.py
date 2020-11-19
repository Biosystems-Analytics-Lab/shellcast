from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import functions

from models import db

class CMU(db.Model):
  __tablename__ = 'cmus'

  id = Column(Integer, primary_key=True)
  cmu_name = Column(String(10), nullable=False)
  created = Column(DateTime, server_default=functions.now())
  updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

  def asDict(self):
    return {
      'cmu_name': self.cmu_name
    }

  def __repr__(self):
    return '<CMU: {}>'.format(self.cmu_name)
