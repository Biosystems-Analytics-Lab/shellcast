from models import db
from models.CMUProbability import CMUProbability
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression, functions


class UserLease(db.Model):
    __tablename__ = "user_leases"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lease_id = Column(String(20), ForeignKey("leases.lease_id"), nullable=False)
    deleted = Column(
        Boolean, server_default=expression.false(), default=False, nullable=False
    )
    created = Column(DateTime, server_default=functions.now())
    updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

    user = relationship("User", back_populates="leases")
    leases = relationship("Lease", back_populates="user_leases")

    def as_dict(self):
        lease = self.leases
        return {
            "lease_id": self.lease_id,
            "grow_area_name": (lease.grow_area_name or "N/A") if lease else "N/A",
            "grow_area_desc": (lease.grow_area_desc or "N/A") if lease else "N/A",
            "cmu_name": (lease.cmu_name or "N/A") if lease else "N/A",
            "rainfall_thresh_in": lease.rainfall_thresh_in if lease else None,
            "latitude": lease.latitude if lease else None,
            "longitude": lease.longitude if lease else None,
            "deleted": self.deleted,
        }

    def get_latest_probability(self):
        lease_prob = (
            db.session.query(CMUProbability)
            .filter_by(lease_id=self.lease_id)
            .order_by(CMUProbability.id.desc())
            .first()
        )
        return lease_prob

    def __repr__(self):
        lease = self.leases
        ga = lease.grow_area_name or "N/A" if lease else "N/A"
        gd = lease.grow_area_desc or "N/A" if lease else "N/A"
        cmu = lease.cmu_name or "N/A" if lease else "N/A"
        prob = lease.rainfall_thresh_in if lease else None
        return (
            f"<UserLease: {self.user_id}, {self.lease_id}, {ga}, {gd}, {cmu}, {prob}>"
        )
