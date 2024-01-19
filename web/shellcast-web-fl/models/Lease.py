from sqlalchemy import Column, Float, String, DateTime, Integer
from sqlalchemy.sql import functions
from sqlalchemy.orm import relationship

from models import db


class Lease(db.Model):
  __tablename__ = 'leases'

  lease_id = Column(String(20), primary_key=True)
  cmu_name = Column(String(10), nullable=False)
  grow_area_name = Column(String(50))
  grow_area_type = Column(String(20))
  waterbody = Column(String(50))
  rainfall_desc = Column(String(50))
  rainfall_thresh_days = Column(Integer)
  rainfall_thresh_in = Column(Float)
  emerg_cond = Column(String(3))
  latitude = Column(Float)
  longitude = Column(Float)
  created = Column(DateTime, server_default=functions.now())
  updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

  user_leases = relationship('UserLease', back_populates='leases')

  def asDict(self):
    return {
      'lease_id': self.lease_id,
      'cmu_name': self.cmu_name,
      'grow_area_name': self.grow_area_name,
      'grow_area_type': self.grow_area_type,
      'waterbody': self.waterbody,
      'rainfall_desc': self.grow_area_desc,
      'rainfall_thresh_days': self.rainfall_thresh_days,
      'rainfall_thresh_in': self.rainfall_thresh_in,
      'emerg_cond': self.emerg_cond,
      'latitude': self.latitude,
      'longitude': self.longitude
    }

  def __repr__(self):
    return '<Lease: {}, {}, {}>'.format(self.lease_id, self.cmu_name, self.grow_area_name)