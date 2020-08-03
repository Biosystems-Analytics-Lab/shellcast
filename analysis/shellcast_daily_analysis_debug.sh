# script name: shellcast_analysis.sh
# purpose of script: this bash script runs python and r scripts for shellcast analysis and save outputs to terminal_data output folder
# author: sheila saia
# date created: 20200701
# email: ssaia@ncsu.edu

# NOTE! need to define folder output paths below

# step 1
# opt/anaconda3/bin/python ndfd_get_forecast_data_script.py | tee opt/analysis/data/tabular/outputs/terminal_data/01_python_output_$(date '+%Y%m%d').txt
python ndfd_get_forecast_data_script.py | tee /Users/sheila/Documents/github_ncsu/shellcast/analysis/data/tabular/outputs/terminal_data/01_get_forecast_output_$(date '+%Y%m%d').txt

# step 2
# /usr/local/bin/Rscript ndfd_convert_df_to_raster_script.R | tee opt/analysis/data/tabular/outputs/terminal_data/02_convert_df_out_$(date '+%Y%m%d').txt
Rscript ndfd_convert_df_to_raster_script.R | tee /Users/sheila/Documents/github_ncsu/shellcast/analysis/data/tabular/outputs/terminal_data/02_convert_df_out_$(date '+%Y%m%d').txt

# step 3
# /usr/local/bin/Rscript ndfd_analyze_forecast_data_script.R | tee opt/analysis/data/tabular/outputs/terminal_data/03_analyze_out_$(date '+%Y%m%d').txt
Rscript ndfd_analyze_forecast_data_script.R | tee /Users/sheila/Documents/github_ncsu/shellcast/analysis/data/tabular/outputs/terminal_data/03_analyze_out_$(date '+%Y%m%d').txt


# QUESTION i need to set up connection for step 4 in this script but how?

# See main README for details on thow to set up both the TCP connection and UNIX socket.

# in home directory (TCP connect - need this for pymysql)
# ./cloud_sql_proxy -instances=MYSQLDB_INSTANCE_ID=tcp:3306
# or could i run it as... (since i'm in the home directory)
# ~/cloud_sql_proxy -instances=MYSQLDB_INSTANCE_ID=tcp:3306

# run in analysis directory (UNIX socket -need this for sqlalchemy)
# ~/cloud_sql_proxy -dir=./cloudsql -instances=MYSQLDB_INSTANCE_ID
# or could i run it as... (this doesn't work)
# ~/cloud_sql_proxy -dir=~/opt/analysis/cloudsql -instances=MYSQLDB_INSTANCE_ID #(this doesn't work)

# step 4
# opt/anaconda3/bin/python gcp_update_mysqldb_script.py | tee opt/analysis/data/tabular/outputs/terminal_data/04_update_db_out_$(date '+%Y%m%d').txt
# python gcp_update_mysqldb_script.py | tee /Users/sheila/Documents/github_ncsu/shellcast/analysis/data/tabular/outputs/terminal_data/04_update_db_out_$(date '+%Y%m%d').txt

# QUESTION i need to close the connection now but how?
