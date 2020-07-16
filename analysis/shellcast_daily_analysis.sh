# script name: shellcast_analysis.sh
# purpose of script: this bash script runs python and r scripts for shellcast analysis and save outputs to terminal_data output folder
# author: sheila saia
# date created: 20200701
# email: ssaia@ncsu.edu

# NOTE! need to define folder output paths below

# step 1
python ndfd_get_forecast_data_script.py | tee ...data/tabular/output/terminal_data/python_output_$(date '+%Y%m%d').txt

# step 2
Rscript ndfd_convert_df_to_raster_script.R | tee ...data/tabular/outputs/terminal_data/convert_df_out_$(date '+%Y%m%d').txt

# step 3
Rscript ndfd_analyze_forecast_data_script.R | tee ...data/tabular/outputs/terminal_data/analyze_out_$(date '+%Y%m%d').txt
