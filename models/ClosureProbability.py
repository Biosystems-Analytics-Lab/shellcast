from models import db
from models.Notification import Notification

class ClosureProbability(db.Model):
  __tablename__ = 'closure_probabilities'
  id = db.Column(db.Integer, primary_key=True)
  lease_id = db.Column(db.Integer, db.ForeignKey('user_leases.id'))
  prob_1d_perc = db.Column(db.Integer)
  prob_2d_perc = db.Column(db.Integer)
  prob_3d_perc = db.Column(db.Integer)
  created = db.Column(db.DateTime, server_default=db.func.now())
  updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

  lease = db.relationship('Lease', back_populates='closureProbabilities')
  notifications = db.relationship('Notification', order_by=Notification.created, back_populates='closureProbability')

  def asDict(self):
    return {
      'prob_1d_perc': self.prob_1d_perc,
      'prob_2d_perc': self.prob_2d_perc,
      'prob_3d_perc': self.prob_3d_perc
    }

  def __repr__(self):
    return '<ClosureProbability({}, {}, {}, {})>'.format(self.lease_id, self.prob_1d_perc, self.prob_2d_perc, self.prob_3d_perc)
