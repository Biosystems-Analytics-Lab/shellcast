from models import db
from models.ClosureProbability import ClosureProbability

class SGAInfo(db.Model):
  __tablename__ = 'sga_info'

  id = db.Column(db.Integer, primary_key=True)
  shellfish_growing_area = db.Column(db.String(3))
  status_id = db.Column(db.Integer)
  rainfall_thresh_in = db.Column(db.Float)
  spatial_data_path = db.Column(db.String(255))
  created = db.Column(db.DateTime)
  updated = db.Column(db.DateTime)

  closureProbabilities = db.relationship('ClosureProbability', order_by=ClosureProbability.created, back_populates='sgaInfo')

  def to_dict(self):
    return {
      'shellfish_growing_area': self.shellfish_growing_area,
      'rainfall_thresh_in': self.rainfall_thresh_in
    }

  def __repr__(self):
    return '<SGAInfo: {}>'.format(self.shellfish_growing_area)
