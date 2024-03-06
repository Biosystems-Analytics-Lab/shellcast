from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import functions, expression
from sqlalchemy.orm import relationship

from models import db
from models.CMUProbability import CMUProbability


class UserLease(db.Model):
  __tablename__ = 'user_leases'

  id = Column(Integer, primary_key=True)
  user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
  lease_id = Column(String(20), ForeignKey('leases.lease_id'), nullable=False)
  deleted = Column(Boolean, server_default=expression.false(), default=False, nullable=False)
  created = Column(DateTime, server_default=functions.now())
  updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

  user = relationship('User', back_populates='leases')
  leases = relationship('Lease', back_populates='user_leases')

  def asDict(self):
    return {
      'lease_id': self.lease_id,
      'parcel_name': self.leases.parcel_name if len(self.leases.parcel_name) > 0 else 'N/A',
      'grow_area_type': self.leases.grow_area_type if len(self.leases.grow_area_type) > 0 else 'N/A',
      'cmu_id': self.leases.cmu_id if len(self.leases.cmu_id) > 0 else 'N/A',
      'rainfall_desc': self.leases.cmus.rainfall_desc if len(self.leases.cmus.rainfall_desc) > 0 else 'N/A',
      'latitude': self.leases.latitude,
      'longitude': self.leases.longitude,
      'deleted': self.deleted
    }

  def getLatestProbability(self):
    leaseProb = db.session.query(CMUProbability).filter_by(cmu_id=self.leases.cmu_id).order_by(CMUProbability.id.desc()).first()
    return leaseProb

  def __repr__(self):
    return '<UserLease: {}, {}, {}, {}, {}, {}>'.format(
      self.user_id,
      self.lease_id,
      self.leases.parcel_name if len(self.leases.parcel_name) > 0 else 'N/A',
      self.leases.grow_area_type if len(self.leases.grow_area_type) > 0 else 'N/A',
      self.leases.cmu_id if len(self.leases.cmu_id) > 0 else 'N/A',
      self.leases.cmus.rainfall_desc if len(self.leases.cmus.rainfall_desc) > 0 else 'N/A'
    )

