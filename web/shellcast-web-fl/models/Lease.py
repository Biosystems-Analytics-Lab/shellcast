import json
from sqlalchemy import Column, Float, String, DateTime, ForeignKey
from sqlalchemy.sql import functions
from sqlalchemy.orm import relationship

from models import db


class Lease(db.Model):
  __tablename__ = 'leases'

  lease_id = Column(String(20), primary_key=True)
  cmu_id = Column(String(10), ForeignKey('cmus.id'), nullable=False)
  parcel_number = Column(String(20))
  parcel_name = Column(String(50))
  grow_area_type = Column(String(20))
  waterbody = Column(String(50))
  latitude = Column(Float)
  longitude = Column(Float)
  created = Column(DateTime, server_default=functions.now())
  updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

  cmus = relationship('CMU', back_populates='leases')
  user_leases = relationship('UserLease', back_populates='leases')
  def asDict(self):
    return {
      'lease_id': self.lease_id,
      'cmu_id': self.cmu_id,
      'parcel_number': self.parcel_number,
      'parcel_name': self.parcel_name,
      'grow_area_type': self.grow_area_type,
      'waterbody': self.waterbody,
      'latitude': self.latitude,
      'longitude': self.longitude
    }

  def __repr__(self):
    return ('<Lease: '
            f'{self.lease_id}, {self.cmu_id}, {self.parcel_number}, '
            f'{self.parcel_name}, {self.grow_area_type}, {self.waterbody}, '
            f'{self.latitude}, {self.latitude}>')
