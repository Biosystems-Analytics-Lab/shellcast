from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from models import db
from models.User import User

class PhoneServiceProvider(db.Model):
  __tablename__ = 'phone_service_providers'

  id = Column(Integer, primary_key=True)
  name = Column(String(30), server_default='', default='')
  mms_gateway = Column(String(30), server_default='', default='')

  users = relationship('User', order_by=User.created, back_populates='service_provider')

  def asDict(self):
    return {
      'id': self.id,
      'name': self.name,
      'mms_gateway': self.mms_gateway
    }

  def __repr__(self):
    return '<Phone Service Provider: {}, {}>'.format(self.name, self.mms_gateway)
