import json
import os
import csv
from pqpf.pqpf_proc_dirs import ProcDirs
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Double
from sqlalchemy.orm import declarative_base


pqpf_dirs = ProcDirs('FL', 'gcp.mysql')
Base = declarative_base()


class Lease(Base):
    __tablename__ = 'leases'
    lease_id = Column(String, primary_key=True)
    cmu_name = Column(String)
    grow_area_name = Column(String)
    grow_area_type = Column(String)
    waterbody = Column(String),
    rainfall_desc = Column(String)
    rainfall_thresh_days = Column(Integer)
    rainfall_thresh_in = Column(Double)
    emerg_cond = Column(String)
    latitude = Column(Double)
    longitude = Column(Double)

    def __str__(self):
        data = {
            'lease_id': self.lease_id,
            'cmu_name': self.cmu_name,
            'grow_area_name': self.grow_area_name,
            'grow_area_type': self.grow_area_type,
            'waterbody': self.waterbody,
            'rainfall_desc': self.rainfall_desc,
            'rainfall_thresh_days': self.rainfall_thresh_days,
            'rainfall_thresh_in': self.rainfall_thresh_in,
            'emerg_cond': self.emerg_cond,
            'latitude': self.latitude,
            'longitude': self.longitude
        }
        return json.dumps(data)


connect_string = 'mysql+pymysql://{}:{}@{}:{}/{}'.format('root', 'L3tm3sql!', '127.0.0.1', '3306', 'shellcast_fl')
engine = create_engine(connect_string)
csv_out_path = os.path.join(pqpf_dirs.inputs_dir, 'fl_individual_lease_and_auz_01182024.csv')

with open(csv_out_path, 'r', encoding='utf-8-sig', newline='') as f:
    next(f)
    reader = csv.reader(f)
    with Session(engine) as session:
        for row in reader:
            lease = Lease(
                lease_id=row[0],
                cmu_name=row[1],
                grow_area_name=row[2],
                grow_area_type=row[3],
                waterbody=row[4],
                rainfall_desc=row[5],
                rainfall_thresh_days=row[6],
                rainfall_thresh_in=row[7],
                emerg_cond=row[8],
                latitude=row[9],
                longitude=row[10]
            )
            print(row)
            session.add(lease)
            session.commit()
