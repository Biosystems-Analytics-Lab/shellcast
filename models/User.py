from models import db
from models.Lease import Lease
from models.Notification import Notification

from sqlalchemy.sql import expression

class User(db.Model):
  __tablename__ = 'users'

  id = db.Column(db.Integer, primary_key=True)
  firebase_uid = db.Column(db.String(28))
  first_name = db.Column(db.String(50))
  last_name = db.Column(db.String(50))
  phone_number = db.Column(db.String(11))
  email = db.Column(db.String(50))
  sms_pref = db.Column(db.Boolean, server_default=expression.false(), default=False)
  email_pref = db.Column(db.Boolean, server_default=expression.false(), default=False)
  created = db.Column(db.DateTime, server_default=db.func.now())
  updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

  leases = db.relationship('Lease', order_by=Lease.created, back_populates='user')
  notifications = db.relationship('Notification', order_by=Notification.created, back_populates='user')

  def asDict(self):
    return {
      'firebase_uid': self.firebase_uid,
      'first_name': self.first_name,
      'last_name': self.last_name,
      'phone_number': self.phone_number,
      'email': self.email,
      'sms_pref': self.sms_pref,
      'email_pref': self.email_pref
    }

  def __repr__(self):
    return '<User: {}>'.format(self.email)
