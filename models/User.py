from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import functions, expression
from sqlalchemy.orm import relationship

from models import db
from models.Lease import Lease
from models.Notification import Notification

class User(db.Model):
  __tablename__ = 'users'

  id = Column(Integer, primary_key=True)
  service_provider_id = Column(Integer, ForeignKey('phone_service_providers.id'))
  firebase_uid = Column(String(28))
  phone_number = Column(String(11))
  email = Column(String(50))
  deleted = Column(Boolean, server_default=expression.false(), default=False)
  created = Column(DateTime, server_default=functions.now())
  updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

  service_provider = relationship('PhoneServiceProvider', back_populates='users')
  leases = relationship('Lease', order_by=Lease.created, back_populates='user')
  notifications = relationship('Notification', order_by=Notification.created, back_populates='user')

  def asDict(self):
    return {
      'service_provider_id': self.service_provider_id,
      'firebase_uid': self.firebase_uid,
      'phone_number': self.phone_number,
      'email': self.email
    }

  def __repr__(self):
    return '<User: {}>'.format(self.email)
