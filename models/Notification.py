from models import db

from sqlalchemy.sql import expression

class Notification(db.Model):
  __tablename__ = 'notification_log'

  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
  address = db.Column(db.String(50))
  notification_text = db.Column(db.String(10000))
  send_success = db.Column(db.Boolean, server_default=expression.true(), default=True)
  response_text = db.Column(db.String(10000))
  created = db.Column(db.DateTime, server_default=db.func.now())

  user = db.relationship('User', back_populates='notifications')

  def asDict(self):
    return {
      'address': self.address,
      'notification_text': self.notification_text,
      'send_success': self.send_success
    }

  def __repr__(self):
    return '<Notification: {}, {}>'.format(self.user_id, self.notification_text)
