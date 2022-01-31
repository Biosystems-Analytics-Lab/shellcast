#!/bin/sh

# script name: shellcast_daily_analysis.sh
# purpose of script: this bash script runs python and r scripts for shellcast analysis and save outputs to terminal_data output folder
# author: sheila saia
# date created: 20200701
# email: ssaia@ncsu.edu

# NOTE! need to define folder output paths below

# source config.sh file (in analysis directory)
source ../config.sh

# make sure that all spawned processes are killed on exit, a kill signal, or an error
trap "exit" INT TERM ERR
trap "kill 0" EXIT

# step 1
# opt/anaconda3/bin/python ndfd_get_forecast_data_script.py | tee opt/analysis/data/tabular/outputs/terminal_data/01_python_output_$(date '+%Y%m%d').txt
${PYTHON_PATH}python3 ndfd_get_forecast_data_script.py | tee ${OUTPUT_PATH}01_get_forecast_output_$(date '+%Y%m%d').txt

# step 2
# /usr/local/bin/Rscript ndfd_convert_df_to_raster_script.R | tee opt/analysis/data/tabular/outputs/terminal_data/02_convert_df_out_$(date '+%Y%m%d').txt
${RSCRIPT_PATH}Rscript ndfd_convert_df_to_raster_script.R | tee ${OUTPUT_PATH}02_convert_df_out_$(date '+%Y%m%d').txt

# open TCP connection for step 4
${CLOUD_SQL_PATH} -instances=${CLOUD_SQL_INSTANCE_NAME}=tcp:${CLOUD_SQL_PORT} &

PID1=$!

# step 3
# /usr/local/bin/Rscript ndfd_analyze_forecast_data_script.R | tee opt/analysis/data/tabular/outputs/terminal_data/03_analyze_out_$(date '+%Y%m%d').txt
${RSCRIPT_PATH}Rscript ndfd_analyze_forecast_data_script.R | tee ${OUTPUT_PATH}03_analyze_out_$(date '+%Y%m%d').txt

# step 4
# opt/anaconda3/bin/python rf_model_precip.py | tee opt/analysis/data/tabular/outputs/terminal_data/04_python_output_$(date '+%Y%m%d').txt
${PYTHON_PATH}python3 rf_model_precip.py | tee ${OUTPUT_PATH}04_rf_model_output_$(date '+%Y%m%d').txt

# See main README for details on thow to set up both the TCP connection.

# login to google cloud platform
# gcloud auth application-default login --client-id-file=/Users/sheila/.config/gcloud/application_default_credentials.json # this is not working either

echo $PID1
# step 5
# opt/anaconda3/bin/python gcp_update_mysqldb_script.py | tee opt/analysis/data/tabular/outputs/terminal_data/05_update_db_out_$(date '+%Y%m%d').txt
${PYTHON_PATH}python3 gcp_update_mysqldb_script.py | tee ${OUTPUT_PATH}05_update_db_out_$(date '+%Y%m%d').txt

# close connections
kill -INT $PID1 #-SIGINT doesn't work here (only in the terminal manually)