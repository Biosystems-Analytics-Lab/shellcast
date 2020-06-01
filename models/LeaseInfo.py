from models import db
from models.ClosureProbability import ClosureProbability

class LeaseInfo(db.Model):
  __tablename__ = 'lease_info'

  id = db.Column(db.Integer, primary_key=True)
  lease_id = db.Column(db.String(10))
  grow_area_name = db.Column(db.String(3))
  rainfall_thresh_in = db.Column(db.Float)
  geo_boundary = db.Column(db.JSON())
  created = db.Column(db.DateTime, server_default=db.func.now())
  updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

  closureProbabilities = db.relationship('ClosureProbability', order_by=ClosureProbability.created, back_populates='leaseInfo')

  def to_dict(self):
    return {
      'shellfish_growing_area': self.grow_area_name,
      'rainfall_thresh_in': self.rainfall_thresh_in
    }

  def __repr__(self):
    return '<LeaseInfo: {}, {}>'.format(self.lease_id, self.grow_area_name)
