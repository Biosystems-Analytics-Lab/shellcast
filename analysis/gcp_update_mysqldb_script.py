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


# %% set paths here

# base path to analysis
# analysis_base_path = "/home/ssaia/analysis/" # set this and uncomment!
# analysis_base_path = "/Users/sheila/Documents/github/shellcast-analysis/"
analysis_base_path = "/Users/sheila/Documents/github_ncsu/shellcast/analysis/"

# base path to data
# data_base_path = "/home/ssaia/shellcast/analysis/data/" # set this and uncomment!
# data_base_path = "/Users/sheila/Documents/bae_shellcast_project/shellcast_analysis/web_app_data/"
data_base_path = "/Users/sheila/Documents/github_ncsu/shellcast/analysis/data/"


# %% use base path

# sga data path
sga_data_path = data_base_path + "tabular/outputs/ndfd_sco_data/sga_calcs/ndfd_sga_calcs.csv"

# lease spatial data
lease_spatial_data_path = data_base_path + "spatial/outputs/ncdmf_data/lease_centroids/lease_centroids_db_wgs84.csv"

# lease data path
lease_data_path = data_base_path + "tabular/outputs/ndfd_sco_data/lease_calcs/ndfd_lease_calcs.csv"

# path to custom functions needed for this script
functions_path = analysis_base_path + "functions/"


# %% load custom functions
exec(open((functions_path + "make_lease_sql_query.py")).read())


# %% load in data

# sga calcs data
sga_data = pandas.read_csv(sga_data_path)

# lease spatial data
lease_spatial_data = pandas.read_csv(lease_spatial_data_path)

# lease calcs data
lease_data = pandas.read_csv(lease_data_path)


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


# %% update sga min and max table

# sga_data = sga_data[1:5] # for testing

# add df to mysql db
sga_data.to_sql('sga_min_max', engine, if_exists = 'append', index = False)

# print status
print("added sga min and max data to mysql db")
# print("did not add sga min and max data to mysql db")

# create cursor to print out status of update
# sga_cursor = connection.cursor()
# execute query
# sga_sql = "SELECT * FROM `sga_min_max`"
# sga_cursor.execute(sga_sql)

# fetch all records and print them
# sga_result = sga_cursor.fetchall()
# for i in sga_result:
#    print(i)


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

    # if there are no new leases to add (from the ncdmf rest api) then skip inserting rows
    if (len(lease_spatial_data_sel) > 0):

        # get sql query
        ncdmf_leases_insert_query = make_lease_sql_query(lease_spatial_data_sel)

        # execute query
        ncdmf_lease_cursor.execute(ncdmf_leases_insert_query)

        # commit changes to remote db
        connection.commit()

        # print when finished
        print("added ncdmf lease data to mysql db")

    else:
        # print when finished
        print("there were no new ncdmf leases to add to mysql db")

else:
    # print that database is empty
    print("the database is empty so leases cannot be added")
    

# %% update closure_probabilities table

# create a cursor to get current leases in db
user_leases_cursor = connection.cursor()

# execute query
user_leases_current_sql = "SELECT id, ncdmf_lease_id FROM user_leases"
user_leases_cursor.execute(user_leases_current_sql)

# save current lease result
user_leases_current_result = user_leases_cursor.fetchall()

# convert to curent lease result to pandas df
user_leases_current_df = pandas.DataFrame(user_leases_current_result)

# lease calcs df select only needed columns 
lease_data_sel = lease_data.drop(columns = 'day').reset_index(drop=True)

# rename to match current lease df
lease_data_sel.columns = ['ncdmf_lease_id', 'prob_1d_perc', 'prob_2d_perc', 'prob_3d_perc']

# set index of lease_data_sel
lease_data_sel_fix = lease_data_sel.set_index('ncdmf_lease_id')

# join lease_data_sel to user_leases_current_df
leases_join_df = user_leases_current_df.set_index(
        'ncdmf_lease_id').join(
                lease_data_sel_fix, how = 'left', on = 'ncdmf_lease_id').set_index(
                        'id').reset_index(drop = False)

# finalize data to add to mysql db
closure_prob_data = pandas.DataFrame({'lease_id' : leases_join_df['id'],
                                     'prob_1d_perc' : leases_join_df['prob_1d_perc'],
                                     'prob_2d_perc' : leases_join_df['prob_2d_perc'],
                                     'prob_3d_perc' : leases_join_df['prob_3d_perc']})
    
# add df to mysql db
closure_prob_data.to_sql('closure_probabilities', engine, if_exists = 'append', index = False)

# print status
print("added user lease data to mysql db")
    
# to_sql can handle NaN to NULL conversion!
# in most cases there should not be NULL values
# but for testing some of the lease id's were made up


# %% dispose engine and close connection

engine.dispose()
connection.close()

# print status
print("gcp connection and engine closed")


# %% extra/draft code

# final fixing up (replacing nan with null)
# closure_prob_data = leases_join_df.replace(numpy.NAN, sqlalchemy.sql.null)

# get ncdmf lease ids
# user_leases_current_ncdmf_ids = user_leases_current_df['ncdmf_lease_id']
# user_leases_current_db_ids = user_leases_current_df['id']

# find lease results for leases in db
# user_leases_data_sel_init = lease_data[lease_data.lease_id.isin(user_leases_current_ncdmf_ids)]
# lease_data_sel_init = lease_data[0:3] # for testing

# find lease id for leases in db
# user_leases_current_db_ids = user_leases_current_df['id']
#user_leases_current_db_ids_sel =user_leases_current_db_ids[user_leases_current_df.ncdmf_lease_id.isin(user_leases_data_sel_init.lease_id)]

# final cleaned up version of lease_dato push to db
# user_leases_data_sel = user_leases_data_sel_init.drop(columns = 'day').reset_index(drop=True)

# use lease data to create closure probabilities dataset
#closure_prob_data = pandas.DataFrame({'lease_id' : user_leases_current_db_ids, # key is actually id column
#                                     'prob_1d_perc' : user_leases_data_sel['prob_1d_perc'],
#                                     'prob_2d_perc' : user_leases_data_sel['prob_2d_perc'],
#                                     'prob_3d_perc' : user_leases_data_sel['prob_3d_perc']})

# create cursor to print out status of update
# lease_cursor = connection.cursor()
# execute query
# lease_sql = "SELECT * FROM `leases`"
# lease_cursor.execute(lease_sql)

# fetch all records and print them
# lease_result = lease_cursor.fetchall()
# for i in lease_result:
#    print(i)
