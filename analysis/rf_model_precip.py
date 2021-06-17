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


# %% load libraries
from config import Config

import pandas as pd
import numpy as np
import joblib

# %% set paths here

# base path to data
data_base_path = Config.DATA_PATH

ndfd_path = data_base_path + "/tabular/outputs/ndfd_sco_data/cmu_calcs/"
ndfd24_path = "ndfd_cmu_calcs_24h.csv"
ndfd48_path = "ndfd_cmu_calcs_48h.csv"
ndfd72_path = "ndfd_cmu_calcs_72h.csv"


# %% load in data

input_data = pd.read_csv(ndfd_path + ndfd24_path)
rain24_df = input_data
input_data = pd.read_csv(ndfd_path + ndfd48_path)
rain48_df = input_data
input_data = pd.read_csv(ndfd_path + ndfd72_path)
rain72_df = input_data


# %% Preprocessing of data

# 24 Hours
x24= rain24_df.loc[:, ['cmu_name', 'pop12_perc', 'qpf_in', 'rainfall_thresh_in', 'month']]
x24['cmu_num'] = x24['cmu_name'].str[1:]
x24 = x24.drop(columns=['cmu_name'],axis=1)
x24 = x24.iloc[:, 0:5]

# 48 Hours
x48= rain48_df.loc[:, ['cmu_name', 'pop12_perc', 'qpf_in', 'rainfall_thresh_in', 'month']]
x48['cmu_num'] = x48['cmu_name'].str[1:]
x48 = x48.drop(columns=['cmu_name'],axis=1)
x48 = x48.iloc[:, 0:5]

# 72 Hours
x72= rain72_df.loc[:, ['cmu_name', 'pop12_perc', 'qpf_in', 'rainfall_thresh_in', 'month']]
x72['cmu_num'] = x72['cmu_name'].str[1:]
x72 = x72.drop(columns=['cmu_name'],axis=1)
x72 = x72.iloc[:, 0:5]


# %% Load trained models

joblib_file_24 = "RF_models/joblib_RL24_Model.pkl"
joblib_file_48 = "RF_models/joblib_RL48_Model.pkl"
joblib_file_72 = "RF_models/joblib_RL72_Model.pkl"

joblib_24_model = joblib.load(joblib_file_24)
joblib_48_model = joblib.load(joblib_file_48)
joblib_72_model = joblib.load(joblib_file_72)


# %% Predict the rainfall

y24_pred = joblib_24_model.predict(x24)
y48_pred = joblib_48_model.predict(x48)
y72_pred = joblib_72_model.predict(x72)


# %% Convert cmu_num to cmu_name

x24['cmu_name'] = x24.apply(lambda row: 'U' + row.cmu_num, axis=1)
x24 = x24.drop(columns=['cmu_num'],axis=1)
x48['cmu_name'] = x48.apply(lambda row: 'U' + row.cmu_num, axis=1)
x48 = x48.drop(columns=['cmu_num'],axis=1)
x72['cmu_name'] = x72.apply(lambda row: 'U' + row.cmu_num, axis=1)
x72 = x72.drop(columns=['cmu_num'],axis=1)

x24['precip_pred'] = y24_pred
x48['precip_pred'] = y48_pred
x72['precip_pred'] = y72_pred

def convertPrecipRisk(df):
    # > 0.9	    Very High	5
    # > 0.75	High	    4
    # > 0.5	    Moderate	3
    # > 0.25	Low	        2
    # < 0.25	Very Low    1
    df['precip_pred'] = np.where(df['precip_pred'] >= (0.9*df['rainfall_thresh_in']), 5, 
                            np.where(df['precip_pred'] >= (0.75*df['rainfall_thresh_in']), 4, 
                                np.where(df['precip_pred'] >= (0.5*df['rainfall_thresh_in']), 3, 
                                    np.where(df['precip_pred'] >= (0.25*df['rainfall_thresh_in']), 2, 1))))

convertPrecipRisk(x24)
convertPrecipRisk(x48)
convertPrecipRisk(x72)


# %% Export the predicted values

# x is the dataframe which has ndfd cmu calculations with all the 24, 48, 72 hour modelled data
x = x24
x['prob_1d_perc']= x24['precip_pred']
x['prob_2d_perc']= x48['precip_pred']
x['prob_3d_perc']= x72['precip_pred']
x = x.drop(columns=['pop12_perc', 'qpf_in', 'rainfall_thresh_in', 'month', 'precip_pred'], axis=1)

ndfd_tabular_data_output_path = data_base_path + "/tabular/outputs/ndfd_sco_data/"

x24.to_csv(ndfd_tabular_data_output_path+'cmu_calcs/x24.csv', index=False)
x48.to_csv(ndfd_tabular_data_output_path+'cmu_calcs/x48.csv', index=False)
x72.to_csv(ndfd_tabular_data_output_path+'cmu_calcs/x72.csv', index=False)
x.to_csv(ndfd_tabular_data_output_path+'cmu_calcs/ndfd_cmu_calcs_rf.csv', index=False)