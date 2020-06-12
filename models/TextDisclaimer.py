from models import db

class TextDisclaimer(db.Model):
  __tablename__ = 'text_disclaimers'

  id = db.Column(db.Integer, primary_key=True)
  webapp_page = db.Column(db.String(50))
  disclaimer_text = db.Column(db.Text)
  created = db.Column(db.DateTime, server_default=db.func.now())
  updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

  def asDict(self):
    return {
      'webapp_page': self.webapp_page,
      'disclaimer_text': self.disclaimer_text
    }

  def __repr__(self):
    return '<TextDisclaimer: {}, {}>'.format(self.webapp_page, self.disclaimer_text)
