from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import functions, expression
from sqlalchemy.orm import relationship

from models import db
from models.PointColType import PointColType

from models.CMUProbability import CMUProbability

class UserLease(db.Model):
  __tablename__ = 'user_leases'
  __table_args__ = (UniqueConstraint('user_id', 'ncdmf_lease_id', name='unique_leases_per_user'),)

  id = Column(Integer, primary_key=True)
  user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
  ncdmf_lease_id = Column(String(20), nullable=False)
  grow_area_name = Column(String(3))
  grow_area_desc = Column(String(50))
  cmu_name = Column(String(10), nullable=False)
  rainfall_thresh_in = Column(Float)
  geometry = Column(PointColType)
  deleted = Column(Boolean, server_default=expression.false(), default=False, nullable=False)
  created = Column(DateTime, server_default=functions.now())
  updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

  user = relationship('User', back_populates='leases')

  def asDict(self):
    return {
      'ncdmf_lease_id': self.ncdmf_lease_id,
      'grow_area_name': self.grow_area_name,
      'grow_area_desc': self.grow_area_desc,
      'cmu_name': self.cmu_name,
      'rainfall_thresh_in': self.rainfall_thresh_in,
      'geometry': self.geometry,
      'deleted': self.deleted
    }

  def getLatestProbability(self):
    leaseProb = db.session.query(CMUProbability).filter_by(cmu_name=self.cmu_name).order_by(CMUProbability.id.desc()).first()
    return leaseProb

  def __repr__(self):
    return '<UserLease: {}, {}, {}, {}>'.format(self.user_id, self.ncdmf_lease_id, self.grow_area_name, self.cmu_name)
