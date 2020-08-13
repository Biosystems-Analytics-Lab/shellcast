from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import functions

from models import db
from models.PointColType import PointColType

class NCDMFLease(db.Model):
  __tablename__ = 'ncdmf_leases'

  id = Column(Integer, primary_key=True)
  ncdmf_lease_id = Column(String(20))
  grow_area_name = Column(String(3))
  rainfall_thresh_in = Column(Float)
  geometry = Column(PointColType)
  created = Column(DateTime, server_default=functions.now())
  updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

  def asDict(self):
    return {
      'ncdmf_lease_id': self.ncdmf_lease_id,
      'grow_area_name': self.grow_area_name,
      'rainfall_thresh_in': self.rainfall_thresh_in,
      'geometry': self.geometry
    }

  def __repr__(self):
    return '<NCDMFLease: {}, {}>'.format(self.ncdmf_lease_id, self.grow_area_name)
