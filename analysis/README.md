# shellcast-analysis


## script run order (daily)

1. ndfd_get_forecast_data_script.py

2. ndfd_convert_df_to_raster_script.R

3. ndfd_analyze_forecast_data_script.R

### shellcast_analysis.sh will run all of daily scripts in order and save updates to the termina\_data directory

```
# sh shellcast_daily_analysis.sh
```

## R packages needed to run these scripts

1. tidyverse - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/tidyverse)

2. lubridate - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/lubridate)

3. sf - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/sf)

4. raster - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/raster)

5. geojsonsf - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/geojsonsf)






## script run order (weekly, when REST API is available)

ncdmf_get_lease_data_script.R (when REST API is available)

ncdmf_tidy_lease_data_script.R (when REST API is available)
