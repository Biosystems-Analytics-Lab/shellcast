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
https://github.com/PyMySQL/PyMySQL
https://pymysql.readthedocs.io/en/latest/


"""

# %% to do list

# TODO how do I connect to mysql db from python


# %% load libraries

import pandas
import pymysql
from sqlalchemy import create_engine


# %% set paths here

# base path to data
# data_base_path = ".../analysis/data/" # set this and uncomment!
data_base_path = "/Users/sheila/Documents/bae_shellcast_project/shellcast_analysis/web_app_data/"


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


# %% create data engines

# create sga data engine
# sga_db_data = 'mysql+mysqldb://' + 'root' + ':' + '12345' + '@' + 'localhost' + ':3306/' + 'sga' + '?charset=utf8mb4'
# sga_engine = create_engine(sga_db_data)
# how do i fill this in?

# create lease data engine
# lease_db_data = 'mysql+mysqldb://' + 'root' + ':' + '12345' + '@' + 'localhost' + ':3306/' + 'lease' + '?charset=utf8mb4'
# lease_engine = create_engine(lease_db_data)
# how do i fill this in?


# %% open connection to MySQL database

# define connection
# define gcp connection variables
#gcp_host = 
#gcp_user = 
#gcp_password =
#gcp_db = 
#gcp_charset = 
# how do i fill this in?

# connect to the MySQL database
connection = pymysql.connect(host = gcp_host,
                             user = gcp_user,
                             password = gcp_password,
                             db = gcp_db,
                             charset = gcp_charset,
                             cursorclass = pymysql.cursors.DictCursor)

## define connection
#connection = pymysql.connect(host='localhost',
#                             user='user',
#                             password='passwd',
#                             db='db',
#                             charset='utf8mb4',
#                             cursorclass=pymysql.cursors.DictCursor)


# %% update sga_min_max table

# create cursor
sga_cursor = connection.cursor()
# Execute the to_sql for writting DF into SQL
sga_data.to_sql('sga_min_max', sga_engine, if_exists='append', index=False)    

# Execute query
sga_sql = "SELECT * FROM `sga_min_max`"
sga_cursor.execute(sga_sql)

# Fetch all the records
sga_result = sga_cursor.fetchall()
for i in sga_result:
    print(i)

engine.dispose()


# %% update leases table

# create cursor
lease_cursor = connection.cursor()
# Execute the to_sql for writting DF into SQL
lease_data.to_sql('leases', lease_engine, if_exists='append', index=False)    

# Execute query
lease_sql = "SELECT * FROM `leases`"
lease_cursor.execute(lease_sql)

# Fetch all the records
lease_result = lease_cursor.fetchall()
for i in lease_result:
    print(i)

engine.dispose()


# %%


# help
# from https://stackoverflow.com/questions/58232218/how-to-insert-a-pandas-dataframe-into-mysql-using-pymysql
# Create dataframe
#data = pd.DataFrame({
#    'book_id':[12345, 12346, 12347],
#    'title':['Python Programming', 'Learn MySQL', 'Data Science Cookbook'],
#    'price':[29, 23, 27]
#})
#
#db_data = 'mysql+mysqldb://' + 'root' + ':' + '12345' + '@' + 'localhost' + ':3306/' \
#       + 'book' + '?charset=utf8mb4'
#engine = create_engine(db_data)
#
## Connect to the database
#connection = pymysql.connect(host='localhost',
#                         user='root',
#                         password='12345',
#                         db='book')    
#
## create cursor
#cursor=connection.cursor()
## Execute the to_sql for writting DF into SQL
#data.to_sql('book_details', engine, if_exists='append', index=False)    
#
## Execute query
#sql = "SELECT * FROM `book_details`"
#cursor.execute(sql)
#
## Fetch all the records
#result = cursor.fetchall()
#for i in result:
#    print(i)
#
#engine.dispose()


# alternative
#data.to_csv("import-data.csv", header=False, index=False, quoting=2, na_rep="\\N")
#
#And then load it at once into the SQL table.
#
#sql = "LOAD DATA LOCAL INFILE \'import-data.csv\' \
#    INTO TABLE book_details FIELDS TERMINATED BY \',\' ENCLOSED BY \'\"\' \
#    (`" +cols + "`)"
#cursor.execute(sql)