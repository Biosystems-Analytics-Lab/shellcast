from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import functions, expression
from sqlalchemy.orm import relationship

from models import db

class Notification(db.Model):
  __tablename__ = 'notification_log'

  id = Column(Integer, primary_key=True)
  user_id = Column(Integer, ForeignKey('users.id'))
  address = Column(String(50))
  notification_text = Column(String(10000))
  send_success = Column(Boolean, server_default=expression.true(), default=True)
  response_text = Column(String(10000))
  created = Column(DateTime, server_default=functions.now())

  user = relationship('User', back_populates='notifications')

  def asDict(self):
    return {
      'address': self.address,
      'notification_text': self.notification_text,
      'send_success': self.send_success
    }

  def __repr__(self):
    return '<Notification: {}, {}>'.format(self.user_id, self.notification_text)
