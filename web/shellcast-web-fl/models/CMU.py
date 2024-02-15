from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import functions
from sqlalchemy.orm import relationship

from models import db

class CMU(db.Model):
  __tablename__ = 'cmus'

  id = Column(String(10), primary_key=True)
  sh_name = Column(String(50), nullable=False)
  created = Column(DateTime, server_default=functions.now())
  # updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())
  def asDict(self):
    return {
      'id': self.id,
      'sh_name': self.sh_name
    }

  def __repr__(self):
    return '<CMU: {}>'.format(self.id, self.sh_name)
