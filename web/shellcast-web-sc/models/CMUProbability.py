from models import db
from sqlalchemy import Column, DateTime, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import functions


class CMUProbability(db.Model):
    __tablename__ = "cmu_probabilities"
    id = Column(Integer, primary_key=True)
    lease_id = Column(String(20), ForeignKey("leases.lease_id"), nullable=False)
    prob_1d_perc = Column(SmallInteger)
    prob_2d_perc = Column(SmallInteger)
    prob_3d_perc = Column(SmallInteger)
    created = Column(DateTime, server_default=functions.now())

    lease = relationship("Lease", backref="cmu_probabilities")

    def as_dict(self):
        return {
            "lease_id": self.lease_id,
            "prob_1d_perc": self.prob_1d_perc,
            "prob_2d_perc": self.prob_2d_perc,
            "prob_3d_perc": self.prob_3d_perc,
        }

    def __repr__(self):
        return f"<CMUProbability: {self.lease_id}, {self.prob_1d_perc}, {self.prob_2d_perc}, {self.prob_3d_perc}>"
