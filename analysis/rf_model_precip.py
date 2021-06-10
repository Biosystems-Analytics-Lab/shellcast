# -*- coding: utf-8 -*-
"""
# ---- script header ----
script name: rf_model_precip.py
purpose of script: This script predicts the given precipitation in inches for the given input parameters.
email: ethedla@ncsu.edu
date created: 20210609

# ---- notes ----
notes:

help:

"""

# %% to do list
# Load the train data and attach it to the script

# %% start script

# %% load libraries
from config import Config
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# %% set paths here

# base path to data
data_base_path = Config.DATA_PATH

# ndfd_path = data_base_path + "/tabular/outputs/ndfd_sco_data/cmu_calcs/"
ndfd_path = data_base_path + "/tabular/outputs/ndfd_sco_data/cmu_calcs/"
ndfd24_path = "ndfd_rocinput_joined_24h.csv"
ndfd48_path = "ndfd_rocinput_joined_48h.csv"
ndfd72_path = "ndfd_rocinput_joined_72h.csv"

# %% load in data

input_data = pd.read_csv(ndfd_path + ndfd24_path)
rain24_df = input_data
input_data = pd.read_csv(ndfd_path + ndfd48_path)
rain48_df = input_data
input_data = pd.read_csv(ndfd_path + ndfd72_path)
rain72_df = input_data
# print("\n24 Hours: \n",rain24_df.head())
# print("\n48 Hours: \n",rain48_df.head())
# print("\n72 Hours: \n",rain72_df.head())

# %% Preprocessing of data

# 24 Hours
x24= rain24_df.loc[:, ['cmu_name', 'pop12_perc', 'qpf_in', 'rainfall_threshold', 'month']]
# y24 = rain24_df.iloc[:, 10]
x24['cmu_num'] = x24['cmu_name'].str[1:]
x24 = x24.drop(columns=['cmu_name'],axis=1)
x24 = x24.iloc[:, 0:5]
print("\n24 Hours with type 1:\n", x24)

# 48 Hours
x48= rain48_df.loc[:, ['cmu_name', 'pop12_perc', 'qpf_in', 'rainfall_threshold', 'month']]
# y48 = rain48_df.iloc[:, 10]
x48['cmu_num'] = x48['cmu_name'].str[1:]
x48 = x48.drop(columns=['cmu_name'],axis=1)
x48 = x48.iloc[:, 0:5]
print("\n48 Hours with type 1:\n", x48)

# 72 Hours
x72= rain72_df.loc[:, ['cmu_name', 'pop12_perc', 'qpf_in', 'rainfall_threshold', 'month']]
# y72 = rain72_df.iloc[:, 10]
x72['cmu_num'] = x72['cmu_name'].str[1:]
x72 = x72.drop(columns=['cmu_name'],axis=1)
x72 = x72.iloc[:, 0:5]
print("\n72 Hours with type 1:\n", x72)

# %% Random Forest Regression

regressor24 = RandomForestRegressor(n_estimators = 100, random_state = 0)
regressor48 = RandomForestRegressor(n_estimators = 100, random_state = 0)
regressor72 = RandomForestRegressor(n_estimators = 100, random_state = 0)


# %% Loading training data


# %% Train and predict the rainfall

regressor24.fit(x, y)
regressor48.fit(x, y)
regressor72.fit(x, y)

y24_pred = regressor24.predict(x24)
y48_pred = regressor48.predict(x48)
y72_pred = regressor72.predict(x72)

# %% Convert cmu_num to cmu_name

x24['cmu_name'] = x24.apply(lambda row: 'U' + row.cmu_num, axis=1)
x24 = x24.drop(columns=['cmu_num'],axis=1)
x48['cmu_name'] = x48.apply(lambda row: 'U' + row.cmu_num, axis=1)
x48 = x48.drop(columns=['cmu_num'],axis=1)
x72['cmu_name'] = x72.apply(lambda row: 'U' + row.cmu_num, axis=1)
x72 = x72.drop(columns=['cmu_num'],axis=1)

# %% Export the predicted values

x24['precip_pred']= y24_pred
x48['precip_pred']= y48_pred
x72['precip_pred']= y72_pred

x24.to_csv(r'x24.csv', index=False)
x48.to_csv(r'x48.csv', index=False)
x72.to_csv(r'x72.csv', index=False)