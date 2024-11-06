from models import db
from sqlalchemy import Column, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import functions


class Lease(db.Model):
    __tablename__ = 'leases'

    lease_id = Column(String(20), primary_key=True)
    cmu_id = Column(String(10), ForeignKey('cmus.id'), nullable=False)
    parcel_name = Column(String(50))
    waterbody = Column(String(50))
    grow_area_type = Column(String(20))
    latitude = Column(Float)
    longitude = Column(Float)
    created = Column(DateTime, server_default=functions.now())
    updated = Column(DateTime, server_default=functions.now(), onupdate=functions.now())

    cmus = relationship('CMU', back_populates='leases')
    user_leases = relationship('UserLease', back_populates='leases')

    def asDict(self):
        return {
            'lease_id': self.lease_id,
            'cmu_id': self.cmu_id,
            'parcel_name': self.parcel_name,
            'waterbody': self.waterbody,
            'grow_area_type': self.grow_area_type,
            'latitude': self.latitude,
            'longitude': self.longitude
        }

    def __repr__(self):
        return ('<Lease: '
                f'{self.lease_id}, {self.cmu_id}, '
                f'{self.parcel_name}, {self.waterbody}, {self.grow_area_type}, '
                f'{self.latitude}, {self.latitude}>')
