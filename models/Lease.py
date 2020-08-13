from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import functions, expression
from sqlalchemy.orm import relationship

from models import db
from models.ClosureProbability import ClosureProbability
from models.PointColType import PointColType

class Lease(db.Model):
  __tablename__ = 'user_leases'

  id = Column(Integer, primary_key=True)
  user_id = Column(Integer, ForeignKey('users.id'))
  ncdmf_lease_id = Column(String(20))
  grow_area_name = Column(String(3))
  rainfall_thresh_in = Column(Float)
  geometry = Column(PointColType)
  email_pref = Column(Boolean, server_default=expression.false(), default=False)
  text_pref = Column(Boolean, server_default=expression.false(), default=False)
  prob_pref = Column(Integer, server_default=expression.literal(75), default=75)
  deleted_by_user = Column(Boolean, server_default=expression.false(), default=False)
  created = Column(DateTime, server_default=functions.now())
  updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

  user = relationship('User', back_populates='leases')
  closureProbabilities = relationship('ClosureProbability', order_by=ClosureProbability.id.desc(), back_populates='lease')

  def asDict(self):
    return {
      'ncdmf_lease_id': self.ncdmf_lease_id,
      'grow_area_name': self.grow_area_name,
      'rainfall_thresh_in': self.rainfall_thresh_in,
      'geometry': self.geometry,
      'email_pref': self.email_pref,
      'text_pref': self.text_pref,
      'prob_pref': self.prob_pref,
      'deleted_by_user': self.deleted_by_user
    }

  def __repr__(self):
    return '<Lease: {}, {}, {}>'.format(self.user_id, self.ncdmf_lease_id, self.grow_area_name)
