from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import functions

from models import db
from models.GeomColType import GeomColType

class GrowArea(db.Model):
  __tablename__ = 'sgas'

  id = Column(Integer, primary_key=True)
  grow_area_name = Column(String(3))
  geometry = Column(GeomColType)
  created = Column(DateTime, server_default=functions.now())
  updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

  def asDict(self):
    return {
      'grow_area_name': self.grow_area_name,
      'geometry': self.geometry,
    }

  def __repr__(self):
    return '<GrowArea: {}>'.format(self.grow_area_name)
