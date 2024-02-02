from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

__all__ = ['CMUProbability', 'Lease', 'Notification', 'PhoneServiceProvider',
           'User', 'UserLease']
