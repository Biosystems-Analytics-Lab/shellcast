# noinspection PyUnresolvedReferences
from models import CMU
from models import db
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import functions


class CMUProbability(db.Model):
    __tablename__ = "cmu_probabilities"

    id = Column(Integer, primary_key=True)
    cmu_id = Column(String(10), ForeignKey("cmus.id"), nullable=False)
    prob_1d_perc = Column(Integer)
    created = Column(DateTime, server_default=functions.now())

    cmus = db.relationship("CMU", back_populates="cmu_probabilities")

    def asDict(self):
        return {
            "cmu_id": self.cmu_id,
            "sh_id": self.cmus.sh_id,
            "sh_name": self.cmus.sh_name,
            "rainfall_desc": self.cmus.rainfall_desc,
            "season": self.cmus.season,
            "prob_1d_perc": self.prob_1d_perc,
            "created": self.created.strftime("%m/%d/%Y"),
        }

    def __repr__(self):
        return "<CMUProbability: {}, {}>".format(
            self.cmu_id, self.cmus.sh_name, self.prob_1d_perc
        )
