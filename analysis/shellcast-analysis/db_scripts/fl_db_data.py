from pathlib import Path

import geopandas as gpd
from sqlalchemy import Table, MetaData
from sqlalchemy import create_engine

ROOT_DIR = Path(__file__).resolve().parent.parent

# DB_USER =
# DB_PASS =
# HOST =
# PORT =

connect_str = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(DB_USER, DB_PASS, HOST, PORT, 'shellcast_fl')
cmu_shp_path = Path(ROOT_DIR, 'data/pqpf/fl/inputs/fl_cmus.shp')
lease_shp_path = Path(ROOT_DIR, 'data/pqpf/fl/inputs/fl_leases.shp')
metadata = MetaData()


def get_cmu_data():
    data_ = []
    gdf = gpd.read_file(str(cmu_shp_path))
    for idx, row in gdf.iterrows():
        row_dict = {'id': row['uid'], 'sh_id': row['sh_id'], 'sh_name': row['sh_name'],
                    'rainfall_desc': row['rainfall'], 'rainfall_thresh_days': row['days'],
                    'rainfall_thresh_in': row['rain_in'], 'season': row['season']}
        data_.append(row_dict)
    return data_


def get_lease_data():
    data_ = []
    gdf = gpd.read_file(str(lease_shp_path))
    for idx, row in gdf.iterrows():
        pn = row['parcel_nam'] if row['parcel_nam'] is not None else ''
        wb = row['waterbody'] if row['waterbody'] is not None else ''
        row_dict = {'lease_id': row['parcel_num'], 'cmu_id': row['uid'], 'parcel_name': pn, 'waterbody': wb,
                    'grow_area_type': row['src'], 'latitude': row['latitude'], 'longitude': row['longitude']}
        data_.append(row_dict)
    return data_


def insert_to_db(table_name, data):
    engine = create_engine(connect_str)
    metadata.create_all(engine)

    cmu_table = Table(table_name, MetaData(), autoload_with=engine)
    cmu_insert = cmu_table.insert()
    with engine.begin() as conn:
        conn.execute(cmu_insert, data)


cmu_data = get_cmu_data()
insert_to_db('cmus', cmu_data)
lease_data = get_lease_data()
insert_to_db('leases', lease_data)
