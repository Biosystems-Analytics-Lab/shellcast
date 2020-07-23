# -*- coding: utf-8 -*-
"""
# ---- script header ----
script name: gcp_update_mysqldb_script.py
purpose of script: This script updates the ShellCast web app MySQL database.
author: sheila saia
email: ssaia@ncsu.edu
date created: 20200716


# ---- notes ----
notes:

help:
pymysql help: https://github.com/PyMySQL/PyMySQL
pymysql docs: https://pymysql.readthedocs.io/en/latest/
gcp docs: https://cloud.google.com/sql/docs/mysql/connect-app-engine-standard


"""

# %% to do list

# TODO update leases


# %% load libraries

import pandas
import pymysql
# from sqlalchemy import create_engine
import sqlalchemy
from config import Config, DevConfig # see config.py file


# %% set paths here

# base path to data
data_base_path = "opt/shellcast/analysis/data/" # set this and uncomment!
# data_base_path = "/Users/sheila/Documents/bae_shellcast_project/shellcast_analysis/web_app_data/"


# %% use base path

# sga data path
sga_data_path = data_base_path + "tabular/outputs/ndfd_sco_data/sga_calcs/ndfd_sga_calcs.csv"

# lease data path
lease_data_path = data_base_path + "tabular/outputs/ndfd_sco_data/lease_calcs/ndfd_lease_calcs.csv"


# %% load in data

# sga data
sga_data = pandas.read_csv(sga_data_path)

# lease data
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


# %% update closure_probabilities table

# create a cursor to get current leases in db
lease_cursor = connection.cursor()

# execute query
lease_current_sql = "SELECT id, ncdmf_lease_id FROM leases"
lease_cursor.execute(lease_current_sql)

# save result
lease_current_result = lease_cursor.fetchall()

# convert to pandas df
lease_current_df = pandas.DataFrame(lease_current_result)

# get ncdmf lease ids
lease_ids_current = lease_current_df['ncdmf_lease_id']
lease_db_ids_current = lease_current_df['id']

# find lease results for leases in db
lease_data_sel_init = lease_data[lease_data.lease_id.isin(lease_ids_current)]
# lease_data_sel_init = lease_data[0:3] # for testing

# final cleaned up version of lease_dato push to db
lease_data_sel = lease_data_sel_init.drop(columns = 'day').reset_index(drop=True)

# use lease data to create closure probabilities dataset
closure_prob_data = pandas.DataFrame({'lease_id' : lease_db_ids_current, # key is actually id column
                                     'prob_1d_perc' : lease_data_sel['prob_1d_perc'],
                                     'prob_2d_perc' : lease_data_sel['prob_2d_perc'],
                                     'prob_3d_perc' : lease_data_sel['prob_3d_perc']})

# add df to mysql db
closure_prob_data.to_sql('closure_probabilities', collection, if_exists = 'append', index = False)

# print status
print("added lease data to mysql db")

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
