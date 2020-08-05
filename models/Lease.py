from models import db
from models.ClosureProbability import ClosureProbability
from models.PointColType import PointColType

from sqlalchemy.sql import expression

class Lease(db.Model):
  __tablename__ = 'user_leases'

  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
  ncdmf_lease_id = db.Column(db.String(20))
  grow_area_name = db.Column(db.String(3))
  rainfall_thresh_in = db.Column(db.Float)
  geometry = db.Column(PointColType)
  email_pref = db.Column(db.Boolean, server_default=expression.false(), default=False)
  text_pref = db.Column(db.Boolean, server_default=expression.false(), default=False)
  prob_pref = db.Column(db.Integer, server_default=expression.literal(75), default=75)
  deleted_by_user = db.Column(db.Boolean, server_default=expression.false(), default=False)
  created = db.Column(db.DateTime, server_default=db.func.now())
  updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

  user = db.relationship('User', back_populates='leases')
  closureProbabilities = db.relationship('ClosureProbability', order_by=ClosureProbability.id.desc(), back_populates='lease')

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
