from models import db

class ClosureProbability(db.Model):
  __tablename__ = 'closure_probabilities'
  id = db.Column(db.Integer, primary_key=True)
  lease_id = db.Column(db.Integer, db.ForeignKey('leases.id'))
  rain_forecast_1d_in = db.Column(db.Float)
  rain_forecast_2d_in = db.Column(db.Float)
  rain_forecast_3d_in = db.Column(db.Float)
  prob_1d_perc = db.Column(db.Integer)
  prob_2d_perc = db.Column(db.Integer)
  prob_3d_perc = db.Column(db.Integer)
  created = db.Column(db.DateTime, server_default=db.func.now())
  updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

  lease = db.relationship('Lease', back_populates='closureProbabilities')

  def to_dict(self):
    return {
      'prob1Day': self.prob_1d_perc,
    }

  def __repr__(self):
    return '<ClosureProbability(id={},lease_id={},perc={})>'.format(self.id, self.lease_id, self.prob_1d_perc)
