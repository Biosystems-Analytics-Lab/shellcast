# shellcast-analysis


## script run order (daily)

1. ndfd_get_forecast_data_script.py

2. ndfd_convert_df_to_raster_script.R

3. ndfd_analyze_forecast_data_script.R

### shellcast_analysis.sh will run all of daily scripts in order and save updates to the termina\_data directory

```
# sh shellcast_daily_analysis.sh

```

## script run order (weekly, when REST API is available)

4. ncdmf_get_lease_data_script.R (when REST API is available)

5. ncdmf_tidy_lease_data_script.R (when REST API is available)

 
# test
