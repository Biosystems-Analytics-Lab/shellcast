# shellcast-analysis

## setting up and running the daily cron job





## cron job script run order

Each day the `shellcast_daily_analysis.sh` will run the following R and Python scripts:

1. `ndfd_get_forecast_data_script.py` - This script gets the forecast and converts it to a pandas dataframe.

2. `ndfd_convert_df_to_raster_script.R` - This script converts the forecast from a pandas dataframe to a raster object.

3. `ndfd_analyze_forecast_data_script.R` - This script takes the raster object as well as other spatial information about the NC coast (shellfish growing area bounds, conditional management bounds, lease bounds, etc.) and does these three levels of calculatoins so they can be used to update the shellcast mysql database.

4. `gcp_update_mysqldb_script.py` - This script takes the data outputs from the previous script and pushes them to the shellcast mysql database.


### running the bash script on its own

To run the bash script not in a cron job (for debugging), use the code below. Outputs from each R and Python script will be saved into the terminal\_data directory.

```
# run this from within the analysis directory

# sh shellcast_daily_analysis.sh
```

## python libraries needed to run these scripts

1. pydap

2. pymysql

3. sqlalchemy

4. 


## r packages needed to run these scripts

1. tidyverse - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/tidyverse)

2. lubridate - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/lubridate)

3. sf - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/sf)

4. raster - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/raster)

5. geojsonsf - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/geojsonsf)






## script run order (weekly, when rest api is available)

ncdmf_get_lease_data_script.R (when rest api is available)

ncdmf_tidy_lease_data_script.R (when rest api is available)
