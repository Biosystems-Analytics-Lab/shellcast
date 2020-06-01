from models import db

class ClosureProbability(db.Model):
  __tablename__ = 'sga_closure_probabilities'
  id = db.Column(db.Integer, primary_key=True)
  sga_id = db.Column(db.Integer, db.ForeignKey('sga_info.id'))
  day = db.Column(db.Integer)
  rain_forecast = db.Column(db.Float)
  prob_percent = db.Column(db.Float)
  color = db.Column(db.String(6))
  created = db.Column(db.DateTime)
  updated = db.Column(db.DateTime)

  sgaInfo = db.relationship('SGAInfo', back_populates='closureProbabilities')

  def to_dict(self):
    return {
      'prob1Day': self.prob_percent,
    }

  def __repr__(self):
    return '<ClosureProbability(id={},sga_id={},perc={})>'.format(self.id, self.sga_id, self.prob_percent)
