from models import db
from models.UserLease import UserLease
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression, functions


class User(db.Model):
    __tablename__ = "users"

    DEFAULT_email_pref = False
    DEFAULT_text_pref = False
    DEFAULT_prob_pref = 3
    DEFAULT_email_consent = False
    DEFAULT_text_consent = False

    id = Column(Integer, primary_key=True)
    firebase_uid = Column(String(28))
    phone_number = Column(String(11))
    email = Column(String(50), nullable=False)
    email_pref = Column(
        Boolean,
        server_default=expression.false(),
        default=DEFAULT_email_pref,
        nullable=False,
    )
    email_consent = Column(
        Boolean,
        server_default=expression.false(),
        default=DEFAULT_email_consent,
        nullable=False,
    )
    text_pref = Column(
        Boolean,
        server_default=expression.false(),
        default=DEFAULT_text_pref,
        nullable=False,
    )
    text_consent = Column(
        Boolean,
        server_default=expression.false(),
        default=DEFAULT_text_consent,
        nullable=False,
    )
    prob_pref = Column(
        Integer,
        server_default=expression.literal(DEFAULT_prob_pref),
        default=DEFAULT_prob_pref,
        nullable=False,
    )
    email_opt_in_date = Column(DateTime)
    text_opt_in_date = Column(DateTime)
    email_opt_out_date = Column(DateTime)
    text_opt_out_date = Column(DateTime)
    email_verified = Column(Boolean, server_default=expression.false(), default=False)
    email_verified_at = Column(DateTime)
    phone_verified = Column(Boolean, server_default=expression.false(), default=False)
    phone_verified_at = Column(DateTime)
    phone_verif_count = Column(Integer, server_default=expression.literal(0), default=0)
    phone_verif_count_date = Column(DateTime)
    deleted = Column(Boolean, server_default=expression.false(), default=False)
    created = Column(DateTime, server_default=functions.now())
    updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

    leases = relationship(
        "UserLease", order_by=UserLease.created, back_populates="user"
    )

    def as_dict(self):
        return {
            "firebase_uid": self.firebase_uid,
            "phone_number": self.phone_number,
            "email": self.email,
            "email_pref": self.email_pref,
            "email_consent": self.email_consent,
            "text_pref": self.text_pref,
            "text_consent": self.text_consent,
            "prob_pref": self.prob_pref,
            "email_verified": self.email_verified,
            "email_verified_at": self.email_verified_at.strftime("%Y-%m-%d %H:%M:%S")
            if self.email_verified_at
            else None,
            "phone_verified": self.phone_verified,
            "phone_verified_at": self.phone_verified_at.strftime("%Y-%m-%d %H:%M:%S")
            if self.phone_verified_at
            else None,
            "phone_verif_count": self.phone_verif_count,
            "phone_verif_count_date": self.phone_verif_count_date.strftime("%Y-%m-%d")
            if self.phone_verif_count_date
            else None,
        }

    def __repr__(self):
        return f"<User: {self.email}>"
