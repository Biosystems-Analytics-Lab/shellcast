# script name: shellcast_analysis.sh
# purpose of script: this bash script runs python and r scripts for shellcast analysis
# author: sheila saia
# date created: 20200701
# email: ssaia@ncsu.edu

# step 1
python ndfd_get_forecast_data_script.py

# step 2
Rscript ndfd_convert_df_to_raster_script.R

# step 3
Rscript ndfd_analyze_forecast_data_script.R
