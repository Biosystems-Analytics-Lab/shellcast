from models import db
from models.Lease import Lease
from models.Notification import Notification

class User(db.Model):
  __tablename__ = 'users'

  id = db.Column(db.Integer, primary_key=True)
  service_provider_id = db.Column(db.Integer, db.ForeignKey('phone_service_providers.id'))
  firebase_uid = db.Column(db.String(28))
  phone_number = db.Column(db.String(11))
  email = db.Column(db.String(50))
  created = db.Column(db.DateTime, server_default=db.func.now())
  updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

  service_provider = db.relationship('PhoneServiceProvider', back_populates='users')
  leases = db.relationship('Lease', order_by=Lease.created, back_populates='user')
  notifications = db.relationship('Notification', order_by=Notification.created, back_populates='user')

  def asDict(self):
    return {
      'firebase_uid': self.firebase_uid,
      'phone_number': self.phone_number,
      'email': self.email
    }

  def __repr__(self):
    return '<User: {}>'.format(self.email)
