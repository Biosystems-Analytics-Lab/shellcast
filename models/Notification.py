from models import db

from sqlalchemy.sql import expression

class Notification(db.Model):
  __tablename__ = 'notification_log'

  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
  closure_prob_id = db.Column(db.Integer, db.ForeignKey('closure_probabilities.id'))
  notification_text = db.Column(db.String(80))
  send_success = db.Column(db.Boolean, server_default=expression.true(), default=True)
  created = db.Column(db.DateTime, server_default=db.func.now())

  user = db.relationship('User', back_populates='notifications')
  closureProbability = db.relationship('ClosureProbability', back_populates='notifications')

  def asDict(self):
    return {
      'notification_text': self.notification_text,
      'send_success': self.send_success
    }

  def __repr__(self):
    return '<Notification: {}, {}, {}>'.format(self.user_id, self.closure_prob_id, self.notification_text)
