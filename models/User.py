from models import db
# from models.Subscription import Subscription
# from models.Notification import Notification

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

  # subscriptions = db.relationship('Subscription', order_by=Subscription.created, back_populates='user')
  # notifications = db.relationship('Notification', order_by=Notification.created, back_populates='user')

  def __repr__(self):
    return '<User: {}>'.format(self.email)
