from models import db
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import functions


class CMUProbability(db.Model):
    __tablename__ = "cmu_probabilities"
    id = Column(Integer, primary_key=True)
    lease_id = Column(String(10), nullable=False)
    prob_1d_perc = Column(Integer)
    prob_2d_perc = Column(Integer)
    prob_3d_perc = Column(Integer)
    created = Column(DateTime, server_default=functions.now())

    def as_dict(self):
        return {
            "lease_id": self.lease_id,
            "prob_1d_perc": self.prob_1d_perc,
            "prob_2d_perc": self.prob_2d_perc,
            "prob_3d_perc": self.prob_3d_perc,
        }

    def __repr__(self):
        return "<CMUProbability: {}, {}, {}, {}>".format(
            self.lease_id, self.prob_1d_perc, self.prob_2d_perc, self.prob_3d_perc
        )
