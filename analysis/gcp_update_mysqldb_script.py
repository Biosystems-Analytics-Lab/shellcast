# -*- coding: utf-8 -*-
"""
# ---- script header ----
script name: gcp_update_mysqldb_script.py
purpose of script: This script updates the ShellCast MySQL database. Specifically it updates
the sga_min_max table, the ncdmf_leases table, and the closure_probabilities table.
email: ssaia@ncsu.edu
date created: 20200716


# ---- notes ----
notes:

help:
pymysql help: https://github.com/PyMySQL/PyMySQL
pymysql docs: https://pymysql.readthedocs.io/en/latest/

"""

# %% to do list



# %% start script

print("starting gcp mysql db update")

# %% load libraries

import pandas
import pymysql
import sqlalchemy
from config import Config, DevConfig # see config.py file
from functions import make_lease_sql_query # see functions.py file


# %% set paths here

# base path to analysis
analysis_base_path = Config.ANALYSIS_PATH

# base path to data
data_base_path = Config.DATA_PATH


# %% use base path

# sga data path
# sga_data_path = data_base_path + "tabular/outputs/ndfd_sco_data/sga_calcs/ndfd_sga_calcs.csv"

# cmu data path
cmu_data_path = data_base_path + "tabular/outputs/ndfd_sco_data/cmu_calcs/ndfd_cmu_calcs_rf.csv"

# lease spatial data
lease_spatial_data_path = data_base_path + "spatial/outputs/ncdmf_data/lease_centroids/lease_centroids_db_wgs84.csv"

# lease data path
# lease_data_path = data_base_path + "tabular/outputs/ndfd_sco_data/lease_calcs/ndfd_lease_calcs.csv"


# %% load in data

# sga calcs data
# sga_data = pandas.read_csv(sga_data_path)

# cmu calcs data
cmu_data = pandas.read_csv(cmu_data_path)

# lease spatial data
lease_spatial_data = pandas.read_csv(lease_spatial_data_path)

# lease calcs data
# lease_data = pandas.read_csv(lease_data_path)


# %% create engine (for sqlalchemy - to upload whole dataframe to mysql db)

# define engine variables
# see config.py for these
db_user = Config.DB_USER
db_pass = Config.DB_PASS
db_name = Config.DB_NAME
cloud_sql_connection_name = Config.CLOUD_SQL_INSTANCE_NAME

# create engine
engine = sqlalchemy.create_engine(
    # Equivalent URL:
    sqlalchemy.engine.url.URL(
        drivername = "mysql+pymysql",
        username = db_user,
        password = db_pass,
        database = db_name,
    ),
)

# engine


# %% open connection (for pymysql - to upload row by row data to mysql db)

# define connection
# see config.py for these
connection = pymysql.connect(host = DevConfig.HOST,
                             user = Config.DB_USER,
                             password = Config.DB_PASS,
                             db = Config.DB_NAME,
                             charset = 'utf8mb4',
                             cursorclass = pymysql.cursors.DictCursor)
# see rest of connection parameters: https://pymysql.readthedocs.io/en/latest/modules/connections.html?highlight=connect#pymysql.connections.Connection

# connection

# %% update cmu probabilities table

# cmu_data = cmu_data[1:5] # for testing

# add df to mysql db
cmu_data.to_sql('cmu_probabilities', engine, if_exists = 'append', index = False)

# print status
print("added cmu data to mysql db")
# print("did not add cmu data to mysql db")


# %% update ncdmf leases table (i.e., all possible leases from the ncdmf rest api)

# only want to add leases that aren't already in the database
# create a cursor to get current leases in db
ncdmf_lease_cursor = connection.cursor()

# define query
ncdmf_leases_current_sql = "SELECT id, ncdmf_lease_id FROM ncdmf_leases"

# execute query
ncdmf_lease_cursor.execute(ncdmf_leases_current_sql)

# save result
ncdmf_leases_current_result = ncdmf_lease_cursor.fetchall()

# if empty then give an error message and don't try to update
if (len(ncdmf_leases_current_result) > 0):
    # convert to pandas df
    ncdmf_leases_current_df = pandas.DataFrame(ncdmf_leases_current_result)

    # get ncdmf lease ids
    ncdmf_leases_current_ids = ncdmf_leases_current_df['ncdmf_lease_id']

    # anti-join to find new ncdmf leases from the ncdmf rest api
    # (i.e., NOT in ncdmf_leases_current_ids and NOT in ncdmf_leases shellcast mysql table)
    lease_spatial_data_sel = lease_spatial_data[~lease_spatial_data['ncdmf_lease_id'].isin(ncdmf_leases_current_ids)].reset_index(drop=True)

    # lease_spatial_data_sel = lease_spatial_data_sel[1:6] # add the first five for now

    # if there are new leases to add then add only those
    if (len(lease_spatial_data_sel) > 0):

        # get sql query
        ncdmf_leases_insert_query = make_lease_sql_query(lease_spatial_data_sel)

        # execute query
        ncdmf_lease_cursor.execute(ncdmf_leases_insert_query)

        # commit changes to remote db
        connection.commit()

        # print when finished
        print("added ncdmf lease data to mysql db")

    # if there are no new leases to add (from the ncdmf rest api) then skip inserting rows
    else:
        # print when finished
        print("there were no new ncdmf leases to add to the mysql db")

# add all data because database is empty
else:
    # format query
    ncdmf_leases_all_insert_query = make_lease_sql_query(lease_spatial_data)

    # execute query
    ncdmf_lease_cursor.execute(ncdmf_leases_all_insert_query)

    # commit changes to remote db
    connection.commit()
    
    # print when finished
    print("the mysql db was empty so all leases were added")


# %% dispose engine and close connection

engine.dispose()
connection.close()

# print status
print("gcp connection and engine closed")
