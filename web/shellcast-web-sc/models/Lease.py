from sqlalchemy import Column, Float, String, DateTime
from sqlalchemy.sql import functions
from sqlalchemy.orm import relationship

from models import db


class Lease(db.Model):
    __tablename__ = "leases"

    lease_id = Column(String(20), primary_key=True)
    grow_area_name = Column(String(3))
    grow_area_desc = Column(String(50))
    cmu_name = Column(String(10), nullable=False)
    rainfall_thresh_in = Column(Float)
    latitude = Column(Float)
    longitude = Column(Float)
    created = Column(DateTime, server_default=functions.now())
    updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

    user_leases = relationship("UserLease", back_populates="leases")

    def asDict(self):
        return {
            "lease_id": self.lease_id,
            "grow_area_name": self.grow_area_name,
            "grow_area_desc": self.grow_area_desc,
            "cmu_name": self.cmu_name,
            "rainfall_thresh_in": self.rainfall_thresh_in,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }

    def __repr__(self):
        return "<Lease: {}, {}, {}>".format(
            self.lease_id, self.grow_area_name, self.cmu_name
        )
