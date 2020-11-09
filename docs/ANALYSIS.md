# ANALYSIS.md

This README file describes the components and set up of the daily analysis cron job that updates the ShellCast web application at [https://go.ncsu.edu/shellcast](https://go.ncsu.edu/shellcast).

## Table of Contents

1. [List of Acronyms](#1.-list-of-acronyms)

2. [Description of Analysis scripts](#2.-description-of-analysis-scripts)

3. [Virtual Computing Lab Set Up](#3.-virtual-computing-lab-set-up)

4. [Cron Job Set Up](#4.-cron-job-set-up)

5. [Cron Job Run Order](#5.-cron-job-run-order)

6. [Description of Cron Job Outputs](#6.-description-of-cron-job-outputs)

## 1. List of Acronyms

- North Carolina Division of Marine Fisheries (NDCMF)
- National Digital Forecast Dataset (NDFD)
- North Carolina State Climate Office (SCO)
- Virtual Computing Lab (VCL)
- Google Cloud Platform (GCP)

## 2. Description of Analysis Scripts

1. `ndfd_get_forecast_data_script.py` - This script gets the NDFD .bin file from the SCO server and converts it to a pandas dataframe.

2. `ndfd_convert_df_to_raster_script.R` - This script converts the NDFD pandas dataframe to a raster object that is used for downstream R analysis.

3. `ndfd_analyze_forecast_data_script.R` - This script takes the raster object as well as other spatial information about the NC coast (shellfish growing area boundaries, conditional management boundaries, lease boundaries, etc.) and does calculations for each scale so they can be used to update the ShellCast MySQL database.

4. `gcp_update_mysqldb_script.py` - This script takes the data outputs from the analysis script and pushes them to the ShellCast MySQL database.

5. `ncdmf_tidy_sga_data_script.R`

6. `ncdmf_tidy_cmu_bounds_script.R`

7. `ncdmf_get_lease_data_script.R` - This script is not yet included but will be created when the NC

8. `ncdmf_tidy_lease_data_script.R` (when rest api is available)

## 3. Virtual Computing Lab (VCL) Set Up

python libraries needed to run these scripts

1. pydap

2. pymysql

3. sqlalchemy

4. pandas

5. numpy

6. datetime

7. requests

8. writer

r packages needed to run these scripts

1. tidyverse - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/tidyverse)

2. lubridate - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/lubridate)

3. sf - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/sf)

4. raster - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/raster)

5. geojsonsf - [package installation info here](https://packagemanager.rstudio.com/client/#/repos/1/packages/geojsonsf)

## 4. Cron Job Set Up

### save gcp credentials (maybe this isn't right....)

Run the code below in the command line. You're web browser will pop open and you'll need to give permission to sign into the email account associated with your account on the shellcast gcp project.

```{bash}
gcloud auth application-default login
```
Copy the location of the json credential file and keep that in a safe location in case you need it later. It will look something like "/Users/sheila/.config/gcloud/application_default_credentials.json".

### setting up the daily cron job

The daily cron job used the `launchd` program, which should be already installed on a Mac, and will run each day at 6am as long as the host computer is on and the program is still loaded. Notifications are sent out at 7am by the Google Cloud Platform cron job.

First, you need to give the terminal permission to run the script. For a Mac, go to Settings > Security & Privacy. Click on Full Disk Access on the left list and go to the Privacy tab. Add Terminal (in Applications > Utilities) to this list. To save this you will have to sign in as an administrator to the machine you're working on. Be sure to lock the administrator privileges before you close the Settings window.

![Full Disk Access Settings Window](/analysis/images/full_disk_access.png)

Next, running a cron job with the `launchd` program requires a correctly formatted plist file (here, `com.shellcast.dailyanalysis.cronjob.plist`). This [blog post]() was especially helpful and the official documentation is [here](https://www.launchd.info/). If you need help debugging the plist script, [LaunchControl](https://www.soma-zone.com/LaunchControl/) is a helpful app (I used the trial version for finding errors).

Last, the bash (.sh) script you're running in the cron job and all the other Python and R scripts that run within the bash script have to be executable. Check to see that they are executable from the terminal window using `ls -l`. You should see "x"s in the far left column for each file (e.g., "-rwxr-xr-x"). If it's no executable (e.g., "-rw-r--r--"), then use `chmod` to make each of them executable.

```{bash}
# make a script executable
chmod +x shellcast_daily_analysis.sh
```

If needed, repeat this use of `chmod` for each of the Python and R scripts listed below in "cron job script run order". All of them need to be executable.

Note, I've successfully run the cron job without the plist file being executable.

### running the daily cron job

When you're ready to run the cron job, do the following:

First, in the terminal, navigate to the LaunchAgents directory.

```{bash}
cd ~/Library/LaunchAgents
```

Second, if the plist file is not there, copy it to this location.

```{bash}
# make sure to change the "..." to the full path
# cp .../analysis/com.shellcast.dailyanalysis.cronjob.plist com.shellcast.dailyanalysis.cronjob.plist

# it will look something like this:
# cp /Users/sheila/Documents/github_ncsu/shellcast/analysis/com.shellcast.dailyanalysis.cronjob.plist com.shellcast.dailyanalysis.cronjob.plist
```

Third, that you're working with the right version using nano or atom.

```{bash}
nano com.shellcast.dailyanalysis.cronjob.plist
```

```{bash}
atom com.shellcast.dailyanalysis.cronjob.plist
```

Fourth, to load the cron job, run the following in the LaunchAgents directory:

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

Also, you can go to `Applications > Utilities > Console` and then look at system log to see current loaded and active programs.

Last, if you need help debugging the plist script, [LaunchControl](https://www.soma-zone.com/LaunchControl/) is a helpful app (I used the trial version for finding errors).

If debugging, I would typically open up LaunchControl to check that that plist file is unloaded. Change the time in the plist file, load it, wait, and then check LaunchControl for status. Sometimes the errors in LaunchControl are not helpful (e.g., Error 1) but other times it will tell you if you need to make the bash script executable. When in down you might have a process running from a previous time you tried to run the script that you have to kill. To do this use htop. Search within htop for "sql" and kill the process. Then start again with checking to make sure the script is unloaded, reload it, wait, etc. It's a little tedious...typical debugging. :/

## 5. Cron Job Run Order

Each day the `shellcast_daily_analysis.sh` will run the following R and Python scripts:

1. `ndfd_get_forecast_data_script.py` - This script gets the forecast and converts it to a pandas dataframe.

2. `ndfd_convert_df_to_raster_script.R` - This script converts the forecast from a pandas dataframe to a raster object.

3. `ndfd_analyze_forecast_data_script.R` - This script takes the raster object as well as other spatial information about the NC coast (shellfish growing area bounds, conditional management bounds, lease bounds, etc.) and does these three levels of calculatoins so they can be used to update the shellcast mysql database.

4. `gcp_update_mysqldb_script.py` - This script takes the data outputs from the previous script and pushes them to the shellcast mysql database.


## running the bash script on its own

To run the bash script not in a cron job (for debugging), use the code below. This must be run from the analysis directory. Outputs from each R and Python script will be saved into the terminal\_data directory.

The bash (.sh) script as well as so all the other Python and R scripts that run within the bash script have to be executable. Check to see that they are executable from the terminal window using `ls -l`. You should see "x"s in the far left column for the file (e.g., "-rwxr-xr-x"). If it's no executable (e.g., "-rw-r--r--"), then use `chmod` to make it executable.

```{bash}
chmod +x shellcast_daily_analysis.sh
```

If needed, repeat this use of `chmod` for each of the Python and R scripts listed below in "cron job script run order".

To run the bash script, open the terminal in the analysis directory and type the following:

```{bash}
sh shellcast_daily_analysis.sh

# for debugging
# sh shellcast_daily_analysis_debug.sh
```

## 6. Description of Cron Job Outputs
