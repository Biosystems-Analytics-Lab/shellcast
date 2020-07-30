#!/bin/sh

# script name: shellcast_analysis.sh
# purpose of script: this bash script runs python and r scripts for shellcast analysis and save outputs to terminal_data output folder
# author: sheila saia
# date created: 20200701
# email: ssaia@ncsu.edu

# NOTE! need to define folder output paths below

# step 1
opt/anaconda3/bin/python ndfd_get_forecast_data_script.py | tee opt/analysis/data/tabular/output/terminal_data/01_python_output_$(date '+%Y%m%d').txt

# step 2
/usr/local/bin/Rscript ndfd_convert_df_to_raster_script.R | tee opt/analysis/data/tabular/outputs/terminal_data/02_convert_df_out_$(date '+%Y%m%d').txt

# step 3
/usr/local/bin/Rscript ndfd_analyze_forecast_data_script.R | tee opt/analysis/data/tabular/outputs/terminal_data/03_analyze_out_$(date '+%Y%m%d').txt
