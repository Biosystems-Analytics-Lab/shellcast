from models import db
from models.PointColType import PointColType

class NCDMFLease(db.Model):
  __tablename__ = 'ncdmf_leases'

  id = db.Column(db.Integer, primary_key=True)
  ncdmf_lease_id = db.Column(db.String(20))
  grow_area_name = db.Column(db.String(3))
  rainfall_thresh_in = db.Column(db.Float)
  geometry = db.Column(PointColType)
  created = db.Column(db.DateTime, server_default=db.func.now())
  updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

  def asDict(self):
    return {
      'ncdmf_lease_id': self.ncdmf_lease_id,
      'grow_area_name': self.grow_area_name,
      'rainfall_thresh_in': self.rainfall_thresh_in,
      'geometry': self.geometry
    }

  def __repr__(self):
    return '<NCDMFLease: {}, {}>'.format(self.ncdmf_lease_id, self.grow_area_name)
