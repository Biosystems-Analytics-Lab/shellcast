from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import functions

from models import db

class TextDisclaimer(db.Model):
  __tablename__ = 'text_disclaimers'

  id = Column(Integer, primary_key=True)
  webapp_page = Column(String(50))
  disclaimer_text = Column(Text)
  created = Column(DateTime, server_default=functions.now())
  updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

  def asDict(self):
    return {
      'webapp_page': self.webapp_page,
      'disclaimer_text': self.disclaimer_text
    }

  def __repr__(self):
    return '<TextDisclaimer: {}, {}>'.format(self.webapp_page, self.disclaimer_text)
