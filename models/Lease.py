from models import db
from models.ClosureProbability import ClosureProbability

from sqlalchemy.sql import expression

class Lease(db.Model):
  __tablename__ = 'user_leases'

  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
  ncdmf_lease_id = db.Column(db.String(20))
  grow_area_name = db.Column(db.String(3))
  rainfall_thresh_in = db.Column(db.Float)
  geo_boundary = db.Column(db.JSON)
  email_pref = db.Column(db.Boolean, server_default=expression.false(), default=False)
  text_pref = db.Column(db.Boolean, server_default=expression.false(), default=False)
  prob_pref = db.Column(db.Integer, server_default=expression.literal(75), default=75)
  created = db.Column(db.DateTime, server_default=db.func.now())
  updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

  user = db.relationship('User', back_populates='leases')
  closureProbabilities = db.relationship('ClosureProbability', order_by=ClosureProbability.created, back_populates='lease')

  def asDict(self):
    return {
      'ncdmf_lease_id': self.ncdmf_lease_id,
      'grow_area_name': self.grow_area_name,
      'rainfall_thresh_in': self.rainfall_thresh_in,
      'geo_boundary': self.geo_boundary,
      'email_pref': self.email_pref,
      'text_pref': self.text_pref,
      'prob_pref': self.prob_pref
    }

  def __repr__(self):
    return '<Lease: {}, {}, {}>'.format(self.user_id, self.ncdmf_lease_id, self.grow_area_name)
