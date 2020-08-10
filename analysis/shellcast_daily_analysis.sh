#!/bin/sh

# script name: shellcast_daily_analysis.sh
# purpose of script: this bash script runs python and r scripts for shellcast analysis and save outputs to terminal_data output folder
# author: sheila saia
# date created: 20200701
# email: ssaia@ncsu.edu

# NOTE! need to define folder output paths below

# make sure that all spawned processes are killed on exit, a kill signal, or an error
trap "exit" INT TERM ERR
trap "kill 0" EXIT

# step 1
# opt/anaconda3/bin/python ndfd_get_forecast_data_script.py | tee opt/analysis/data/tabular/outputs/terminal_data/01_python_output_$(date '+%Y%m%d').txt
/Users/sheila/opt/anaconda3/bin/python ndfd_get_forecast_data_script.py | tee /Users/sheila/Documents/github_ncsu/shellcast/analysis/data/tabular/outputs/terminal_data/01_get_forecast_output_$(date '+%Y%m%d').txt

# step 2
# /usr/local/bin/Rscript ndfd_convert_df_to_raster_script.R | tee opt/analysis/data/tabular/outputs/terminal_data/02_convert_df_out_$(date '+%Y%m%d').txt
/usr/local/bin/Rscript ndfd_convert_df_to_raster_script.R | tee /Users/sheila/Documents/github_ncsu/shellcast/analysis/data/tabular/outputs/terminal_data/02_convert_df_out_$(date '+%Y%m%d').txt

# step 3
# /usr/local/bin/Rscript ndfd_analyze_forecast_data_script.R | tee opt/analysis/data/tabular/outputs/terminal_data/03_analyze_out_$(date '+%Y%m%d').txt
/usr/local/bin/Rscript ndfd_analyze_forecast_data_script.R | tee /Users/sheila/Documents/github_ncsu/shellcast/analysis/data/tabular/outputs/terminal_data/03_analyze_out_$(date '+%Y%m%d').txt

# See main README for details on thow to set up both the TCP connection.

# login to google cloud platform
# gcloud auth application-default login --client-id-file=/Users/sheila/.config/gcloud/application_default_credentials.json # this is not working either

# open TCP connection for step 4
/Users/sheila/cloud_sql_proxy -instances=ncsu-shellcast:us-east1:ncsu-shellcast-database=tcp:3306 &

PID1=$!

echo $PID1

# wait 3 seconds to make sure connections are open
sleep 5s

# step 4
# opt/anaconda3/bin/python gcp_update_mysqldb_script.py | tee opt/analysis/data/tabular/outputs/terminal_data/04_update_db_out_$(date '+%Y%m%d').txt
/Users/sheila/opt/anaconda3/bin/python gcp_update_mysqldb_script.py | tee /Users/sheila/Documents/github_ncsu/shellcast/analysis/data/tabular/outputs/terminal_data/04_update_db_out_$(date '+%Y%m%d').txt

# close connections
kill -INT $PID1 #-SIGINT doesn't work here (only in the terminal manually)
