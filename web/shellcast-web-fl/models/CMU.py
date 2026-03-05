from models import db
from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import functions


class CMU(db.Model):
    __tablename__ = "cmus"

    id = Column(String(10), primary_key=True)
    sh_id = Column(String(10), nullable=False)
    sh_name = Column(String(50))
    rainfall_desc = Column(String(100))
    rainfall_thresh_days = Column(Integer, nullable=False)
    rainfall_thresh_in = Column(Float, nullable=False)
    season = Column(String(100))
    created = Column(DateTime, server_default=functions.now())

    cmu_probabilities = relationship("CMUProbability", back_populates="cmus")
    leases = relationship("Lease", back_populates="cmus")

    # updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())
    def as_dict(self):
        return {
            "id": self.id,
            "sh_id": self.sh_id,
            "sh_name": self.sh_name,
            "rainfall_desc": self.rainfall_desc.replace('"', '"'),
            "rainfall_thresh_days": self.rainfall_thresh_days,
            "rainfall_thresh_in": self.rainfall_thresh_in,
            "season": self.season,
        }

    def __repr__(self):
        return (
            "<CMU: "
            f"{self.id}, {self.sh_id}, {self.sh_name}, {self.rainfall_desc}, "
            f"{self.rainfall_thresh_days}, {self.rainfall_thresh_in}, {self.season}>"
        )
