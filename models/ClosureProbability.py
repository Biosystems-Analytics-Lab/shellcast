from models import db

class ClosureProbability(db.Model):
  __tablename__ = 'sga_closure_probabilities'
  id = db.Column(db.Integer, primary_key=True)
  sga_id = db.Column(db.Integer)
  day = db.Column(db.Integer)
  rain_forecast = db.Column(db.Float)
  prob_percent = db.Column(db.Float)
  color = db.Column(db.String(6))
  created = db.Column(db.DateTime)
  updated = db.Column(db.DateTime)

  def __repr__(self):
    return '<SGAClosureProbability: {}>'.format(self.id)
