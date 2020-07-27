# -*- coding: utf-8 -*-
"""
# ---- script header ----
script name: gcp_update_mysqldb_script.py
purpose of script: This script updates the ShellCast web app MySQL database. Specifically it updates the sga_min_max table, the ncdmf_leases table, and the closure_probabilities table.
author: sheila saia
email: ssaia@ncsu.edu
date created: 20200716


# ---- notes ----
notes:

help:
pymysql help: https://github.com/PyMySQL/PyMySQL
pymysql docs: https://pymysql.readthedocs.io/en/latest/
gcp docs: https://cloud.google.com/sql/docs/mysql/connect-app-engine-standard
geoalchemy2: https://stackoverflow.com/questions/38361336/write-geodataframe-into-sql-database

# install geopandas (in the shell)
conda install -c conda-forge geopandas

# install geoalchemy2 (in the shell)
conda install -c conda-forge geoalchemy2


"""

# %% to do list

# TODO update leases


# %% load libraries

import pandas
import geopandas
import pymysql
# from sqlalchemy import create_engine
import sqlalchemy
from geoalchemy2 import Geometry, WKTElement
from config import Config, DevConfig # see config.py file


# %% set paths here

# base path to data
# data_base_path = "opt/shellcast/analysis/data/" # set this and uncomment!
data_base_path = "/Users/sheila/Documents/bae_shellcast_project/shellcast_analysis/web_app_data/"


# %% use base path

# sga data path
sga_data_path = data_base_path + "tabular/outputs/ndfd_sco_data/sga_calcs/ndfd_sga_calcs.csv"

# lease spatial data
lease_spatial_data_path = data_base_path + "spatial/outputs/ncdmf_data/lease_centroids/lease_centroids_simple_wgs84.geojson"

# lease data path
lease_data_path = data_base_path + "tabular/outputs/ndfd_sco_data/lease_calcs/ndfd_lease_calcs.csv"


# %% load in data

# sga calcs data
sga_data = pandas.read_csv(sga_data_path)

# lease spatial data
lease_spatial_data = geopandas.read_file(lease_spatial_data_path)

# lease calcs data
lease_data = pandas.read_csv(lease_data_path)


# %% create engine collection (for sqlalchemy)

# define engine variables
# see config.py for these
db_user = Config.DB_USER
db_pass = Config.DB_PASS
db_name = DevConfig.DB_NAME
db_socket_dir = DevConfig.DB_UNIX_SOCKET_PATH_PREFIX
cloud_sql_connection_name = Config.CLOUD_SQL_INSTANCE_NAME

# create collection
collection = sqlalchemy.create_engine(
    # Equivalent URL:
    # mysql+pymysql://<db_user>:<db_pass>@/<db_name>?unix_socket=<socket_path>/<cloud_sql_instance_name>
    sqlalchemy.engine.url.URL(
        drivername="mysql+pymysql",
        username=db_user,  # e.g. "my-database-user"
        password=db_pass,  # e.g. "my-database-password"
        database=db_name,  # e.g. "my-database-name"
        query={
            "unix_socket": "{}/{}".format(
                db_socket_dir,  # e.g. "/cloudsql"
                cloud_sql_connection_name)  # i.e "<PROJECT-NAME>:<INSTANCE-REGION>:<INSTANCE-NAME>"
        }
    ),
    # ... Specify additional properties here.
)

# collection


# %% open connection (for pymysql)

# define connection
# see config.py for these
connection = pymysql.connect(host = DevConfig.HOST,
                             user = Config.DB_USER,
                             password = Config.DB_PASS,
                             db = DevConfig.DB_NAME,
                             charset = 'utf8mb4',
                             cursorclass = pymysql.cursors.DictCursor)
# see rest of connection parameters: https://pymysql.readthedocs.io/en/latest/modules/connections.html?highlight=connect#pymysql.connections.Connection

# connection


# %% update sga min and max table

# add df to mysql db
sga_data.to_sql('sga_min_max', collection, if_exists = 'append', index = False)

# print status
print("added sga min and max data to mysql db")

# create cursor to print out status of update
# sga_cursor = connection.cursor()
# execute query
# sga_sql = "SELECT * FROM `sga_min_max`"
# sga_cursor.execute(sga_sql)

# fetch all records and print them
# sga_result = sga_cursor.fetchall()
# for i in sga_result:
#    print(i)

# %% update ncdmf leases table (i.e., all possible leases from the NC DMF REST API)

# only want to add leases that aren't already in the database
# create a cursor to get current leases in db
ncdmf_lease_cursor = connection.cursor()

# define query
ncdmf_leases_current_sql = "SELECT id, ncdmf_lease_id FROM ncdmf_leases"

# execute query
ncdmf_lease_cursor.execute(ncdmf_leases_current_sql)

# save result
ncdmf_leases_current_result = ncdmf_lease_cursor.fetchall()

# convert to pandas df
ncdmf_leases_current_df = pandas.DataFrame(ncdmf_leases_current_result)

# get ncdmf lease ids
ncdmf_leases_current_ids = ncdmf_leases_current_df['ncdmf_lease_id']

# anti-join to find ones that are new (i.e., NOT in ncdmf_leases_current_ids)
lease_spatial_data_sel = lease_spatial_data[~lease_spatial_data['ncdmf_lease_id'].isin(ncdmf_leases_current_ids)].reset_index(drop=True)

# if lease_spatial_data_sel length is zero then don't push updates to mysql database
if (len(lease_spatial_data_sel['ncdmf_lease_id']) > 0):
    # define coordinate reference system (crs same as sric)
    wgs84_epsg = 4326
    
    # create a geom with SRID
    def create_wkt_element(geom):
        return WKTElement(geom.wkt, srid = wgs84_epsg)
    
    # assign crs to geometry column
    lease_spatial_data_sel['geometry'] = lease_spatial_data_sel['geometry'].apply(create_wkt_element)
    
    # Use 'dtype' to specify column's type
    # For the geom column, we will use GeoAlchemy's type 'Geometry'
    lease_spatial_data_sel.to_sql('ncdmf_leases', collection, if_exists = 'append', index = False, 
                                  dtype={'geometry': Geometry('POINT', srid = wgs84_epsg)})
    
    # print when finished
    print("added ncdmf lease data to mysql db")
    
else:
    #print when finished
    print("no ncdmf lease data updates required")


# %% update closure_probabilities table

# create a cursor to get current leases in db
user_leases_cursor = connection.cursor()

# execute query
user_leases_current_sql = "SELECT id, ncdmf_lease_id FROM user_leases"
user_leases_cursor.execute(user_leases_current_sql)

# save result
user_leases_current_result = user_leases_cursor.fetchall()

# convert to pandas df
user_leases_current_df = pandas.DataFrame(user_leases_current_result)

# get ncdmf lease ids
user_leases_current_ncdmf_ids = user_leases_current_df['ncdmf_lease_id']
user_leases_current_db_ids = user_leases_current_df['id']

# find lease results for leases in db
user_leases_data_sel_init = lease_data[lease_data.lease_id.isin(user_leases_current_ncdmf_ids)]
# lease_data_sel_init = lease_data[0:3] # for testing

# final cleaned up version of lease_dato push to db
user_leases_data_sel = user_leases_data_sel_init.drop(columns = 'day').reset_index(drop=True)

# use lease data to create closure probabilities dataset
closure_prob_data = pandas.DataFrame({'lease_id' : user_leases_current_db_ids, # key is actually id column
                                     'prob_1d_perc' : user_leases_data_sel['prob_1d_perc'],
                                     'prob_2d_perc' : user_leases_data_sel['prob_2d_perc'],
                                     'prob_3d_perc' : user_leases_data_sel['prob_3d_perc']})

# add df to mysql db
closure_prob_data.to_sql('closure_probabilities', collection, if_exists = 'append', index = False)

# print status
print("added user lease data to mysql db")

# create cursor to print out status of update
# lease_cursor = connection.cursor()
# execute query
# lease_sql = "SELECT * FROM `leases`"
# lease_cursor.execute(lease_sql)

# fetch all records and print them
# lease_result = lease_cursor.fetchall()
# for i in lease_result:
#    print(i)


# %% dispose engine and close connection

collection.dispose()
connection.close()

# print status
print("gcp connection and collection closed")
