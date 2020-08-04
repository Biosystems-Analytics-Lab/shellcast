# shellcast-analysis

## setting up and running the daily cron job

The daily cron job used the `launchd` program, which should be already installed on a Mac, and will run each day at 7am as long as the host computer is on and the program is still loaded.

Running a cron job with the `launchd` program requires a correctly formatted plist file (here, `com.shellcast.dailyanalysis.cronjob.plist`). This [blog post]() was especially helpful and the official documentation is [here](https://www.launchd.info/). Last, if you need help debugging the plist script, [LaunchControl](https://www.soma-zone.com/LaunchControl/) is a helpful app (I used the trial version for finding errors).

In the terminal, navigate to the LaunchAgents directory:
```{bash}
cd ~/Library/LaunchAgents
```

If `com.shellcast.dailyanalysis.cronjob.plist` file is not there, copy it here, using:
```{bash}
cp .../analysis/com.shellcast.dailyanalysis.cronjob.plist com.shellcast.dailyanalysis.cronjob.plist

# cp /Users/sheila/Documents/github_ncsu/shellcast/analysis/com.shellcast.dailyanalysis.cronjob.plist com.shellcast.dailyanalysis.cronjob.plist
```

Check that you're working with the right version using nano.
```{bash}
nano com.shellcast.dailyanalysis.cronjob.plist
```

To load the cron job, run the following in the LaunchAgents directory:
```{bash}
launchctl load com.shellcast.dailyanalysis.cronjob.plist
```

To stop the cron job, run the following in the LaunchAgents directory:
```{bash}
launchctl unload com.shellcast.dailyanalysis.cronjob.plist
```

To see if a LaunchAgent is loaded you can use:
```{bash}
launchctl list
```

Also, you can go to `Applications > Utilities > Console` and then look at system log to see current loaded and active programs. Last, if you need help debugging the plist script, [LaunchControl](https://www.soma-zone.com/LaunchControl/) is a helpful app (I used the trial version for finding errors).


## cron job script run order

Each day the `shellcast_daily_analysis.sh` will run the following R and Python scripts:

1. `ndfd_get_forecast_data_script.py` - This script gets the forecast and converts it to a pandas dataframe.

2. `ndfd_convert_df_to_raster_script.R` - This script converts the forecast from a pandas dataframe to a raster object.

3. `ndfd_analyze_forecast_data_script.R` - This script takes the raster object as well as other spatial information about the NC coast (shellfish growing area bounds, conditional management bounds, lease bounds, etc.) and does these three levels of calculatoins so they can be used to update the shellcast mysql database.

4. `gcp_update_mysqldb_script.py` - This script takes the data outputs from the previous script and pushes them to the shellcast mysql database.


### running the bash script on its own

To run the bash script not in a cron job (for debugging), use the code below. Outputs from each R and Python script will be saved into the terminal\_data directory. This script must be executable so you might have to check script permissions in the terminal window using `ls -l` and if not executable, then use `chmod -x shellcast_daily_analysis.sh` to make it executable.

```{bash}
# run this from within the analysis directory

# sh shellcast_daily_analysis.sh
```

## python libraries needed to run these scripts

1. pydap

2. pymysql

3. sqlalchemy

4. pandas

5. numpy

6. datetime

7. requests

8. writer


## r packages needed to run these scripts

1. tidyverse - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/tidyverse)

2. lubridate - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/lubridate)

3. sf - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/sf)

4. raster - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/raster)

5. geojsonsf - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/geojsonsf)






## script run order (weekly, when rest api is available)

ncdmf_get_lease_data_script.R (when rest api is available)

ncdmf_tidy_lease_data_script.R (when rest api is available)
