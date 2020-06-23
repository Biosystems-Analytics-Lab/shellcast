from models import db

class SGAMinMaxProbability(db.Model):
  __tablename__ = 'sga_min_max'

  id = db.Column(db.Integer, primary_key=True)
  grow_area_name = db.Column(db.String(3))
  min_1d_prob = db.Column(db.Integer)
  max_1d_prob = db.Column(db.Integer)
  min_2d_prob = db.Column(db.Integer)
  max_2d_prob = db.Column(db.Integer)
  min_3d_prob = db.Column(db.Integer)
  max_3d_prob = db.Column(db.Integer)
  created = db.Column(db.DateTime)
  updated = db.Column(db.DateTime)

  def asDict(self):
    return {
      'min_1d_prob': self.min_1d_prob,
      'max_1d_prob': self.max_1d_prob,
      'min_2d_prob': self.min_2d_prob,
      'max_2d_prob': self.max_2d_prob,
      'min_3d_prob': self.min_3d_prob,
      'max_3d_prob': self.max_3d_prob,
    }

  def __repr__(self):
    return '<SGAMinMax: {}>'.format(self.grow_area_name)
