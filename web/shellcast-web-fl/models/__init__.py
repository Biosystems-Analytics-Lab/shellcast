from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models so SQLAlchemy can resolve relationship("...") strings.
# Order: base models first, then those that reference them (avoids circular import issues).
from models.CMU import CMU
from models.CMUProbability import CMUProbability
from models.Lease import Lease
from models.Notification import Notification
from models.User import User
from models.UserLease import UserLease

__all__ = [
    "db",
    "CMU",
    "CMUProbability",
    "Lease",
    "Notification",
    "User",
    "UserLease",
]
