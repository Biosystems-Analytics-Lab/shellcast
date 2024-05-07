# ANALYSIS.md

This markdown file describes the components and set up of the daily analysis CRON job that updates the ShellCast web application at [https://go.ncsu.edu/shellcast](https://go.ncsu.edu/shellcast).

## Table of Contents

0. [Background](#0-background)
1. [List of Acronyms](#1-list-of-acronyms)
2. [Description of Analysis Scripts](#2-description-of-analysis-scripts)
3. [CRON Job Set Up](#4-cron-job-set-up)
4. [Pushing Changes to GitHub](#7-pushing-changes-to-github)
5. [Updating Leases](#8-updating-leases)
9. [Contact Information](#9-contact-information)

## 0. Background
The main purpose of the scripts in the analysis folder is to: (1) pull Probabilistic Quantitative Precipitation 
Forecasting (PQPF) data from a remote server at the NOAA, (2) do geospatial analysis based on given thresholds 
determined by organizations, (3) classify step 2 values, and (4) update the ShellCast MySQL database. For a schematic 
representation of this workflow, including how they relate to other major components of the ShellCast web application,
see the ShellCast [architecture overview flowchart](/../../#2-architecture-overview). The current ShellCast forecast is 
for North Carolina, South Carolina, and Florida.

The analysis daily CRON job ensures that the three steps described above will run every day at 6:40 am ET on the 
temporary project computer (iMac).  


## 1. List of Acronyms

- North Carolina State University (NCSU)
- North Carolina Division of Marine Fisheries (NCDMF)
- National Digital Forecast Dataset (NDFD)
- North Carolina State Climate Office (SCO)
- Google Cloud Platform (GCP)
- National Oceanic and Atmospheric Administration (NOAA)
- Climate Data Operators (CDO)
- Probabilistic Quantitative Precipitation Forecasting (PQPF)
- Shellfish Harvested Area (SHA)
- Contiguous United States, and as the 48 contiguous states (CONUS)

## 2. Analysis and Scripts

### Preprocessing input data

ArcGIS Pro is used to preprocess the input data. Modelbuilder was used to create the processing tools for each state. Assigning shellfish harvested area rainfall threshold to leases within the area, checking and fixing geometry, and assigning appropriate column names to attributes tables are among the tasks. Contact the project PI for ArcGIS Pro project files. 

*Note*: Input data needs to be updated periodically. Currently, NCSU is responsible for updating input data. We may be able to automate updates if organizations publish shapefiles online in the data format we require.

### Analysis

Each state has its own geospatial analysis, however, North Carolina and Florida analysis share the same analogy; 1) finding the probability of precipitation from PQPF data for each lease location, 2) finding the mean value within the SHA area, 3) classifying the values into very low, low, moderate, high, and very high, and 4) saving categorized values to a remote MySQL database. Analysis for Florida adds complexity due to duration-based rainfall thresholds (e.g. 5 days > 3.5"). In addition to PQPF, daily quality controlled rainfall estimates are used to calculate rainfall accumulation. 

In South Carolina analysis, SHA are considered lease areas. The mean PQPF for each SHA is calculated using geospatial statistics, classified, and then stored remotely.

### Scripts

* `src`-  all analysis code
  * `{state}_pqpf` - code for geospatial analysis specific to a state
  * `pqpf` - code for common processes
* `shellcast-analysis/{state}_main.py` -  This script runs geospatial analysis and saves the output data to a remote MySQL server. 
  * Prerequisites : create a virtual environment and connect to a remote MySQL server.
* `setup_logging.py` and `{state}_logging.yaml` - Logs file settings
* `config.ini` - A configuration file for analyzing data and setting up remote database servers.
* `config.sh` -  This script specifies the script path and the remote server name. The `analysis_run.sh` file refers to this file.
* `analysis_run.sh` -  This script is configured to run a cron job. The script activates the virtual environment, connects to the remote MySQL database, and runs `{state}_main.py`. Modifying this script file is recommended if you wish to run a state analysis only by commenting out the other states.

## 3. Data

**Data**

1. PQPF  (NOAA) Grib2 format
2. Daily quality controlled rainfall estimates (NOAA) Grib1 format - FL only

**Input Data**

1. NC lease and SHA shapefiles
2. SC SHA shapefiles
3. FL lease and SHA shapefiles



## 4. Development Environment Set Up

### 4.1 Install and initialize Google Cloud SDK

The Google Cloud SDK is principally a command line tool that allows you to interact with Google Cloud from your local machine and perform various tasks. You can download, install, and initialize the Google Cloud SDK by following [these instructions](https://cloud.google.com/sdk/docs/quickstart).

### 4.2 Download Cloud SQL proxy

You can download and setup the Cloud SQL proxy by following [these instructions](https://cloud.google.com/sql/docs/mysql/quickstart-proxy-test#install-proxy). Take note of where you download the proxy script. You will need to run it often, so keep it in a place that's easy to reference. Install MySQL by following [these instructions](https://downloads.mysql.com/archives/community/). Optionaly, iinstall [MySQL Workbench](https://dev.mysql.com/downloads/workbench) to visualize and query the database.

### 4.3 Clone the ShellCast GitHub repository

Clone the GitHub repository to your machine by running `git clone https://github.ncsu.edu/biosystemsanalyticslab/shellcast.git`.  It's recommended that you clone the repository to a relatively shallow path in your file system.  If the path to the repo is too long, then it can cause issues with Unix sockets (see [Use the Cloud SQL proxy (TCP and Unix socket)](#51-use-the-cloud-sql-proxy-tcp-and-unix-socket)).

### 4.4 Setup Python virtual environment

Use environment management tool of your choice. Set the latest version of Python that has been tested with [pygrib](https://pypi.org/project/pygrib/) package.

### 4.5 Download and Compile Wgrib2

Wgrib2 is used to crop CONUS PQPF data according to the area of interest. 

Download the application on [here](https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2) and follow [these instructions](https://www.ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/INSTALLING). For Mac user, this website [theweatherguy blog](https://theweatherguy.net/blog/how-to-install-and-compile-wgrib2-on-macos-monterey-ventura/) might help. It is necessary to install the gcc/gfortran compilers for Wgrib2 compilation. You can download `gcc` using Homebrew on Mac by running `brew install gcc`. It contains gcc, g++, gfortran, etc. 

### 4.6 Download and Compile NCEPLIBS GRIB Utility and Dependencies

`cnvgrib` converts daily quality controlled rainfall estimates from Grib1 to Grib2 format. 

Clone `NCEPLIB-grib_util` from [NOAA-EMC GitHub](https://github.com/NOAA-EMC/NCEPLIBS-grib_util) website. The steps for compiling dependencies and utility can be found in ncep_lib_utils.sh. It is recommended that each dependency be compiled separately to ensure successful compilation. The third-party libraries Jasper, libpng, and zlib must be installed before the dependencies are compiled. 

For example, Homebrewer on Mac

```
brew install jasper
```

```
brew install libpng
```

``` 
brew install zlib
```

### 4.7 Install CDO 

Daily quality controlled rainfall estimates are processed using CDO. 

You can download CDO using Homebrew on Mac by running ```brew install cdo```

## 5. CRON Job Set Up

Tools for CRON jobs can be chosen freely by developers. Currently, ShellCast analyses are run on the temporary iMac computer using the `crontab` command. 

```TODO: Add how to set crontab and how to debug **** or run-as-cron```

## 6. Pushing Changes to GitHub

When appropriate, changes need to be pushed to the NCSU Enterprise GitHub repository **as well as** the GitHub (public) respository as described in the [DEVELOPER.md documentation](/docs/DEVELOPER.md).

## 7. Updating Leases

Untill we're able to get REST API access from the North Carolina Division of Marine Fisheries (NCDMF), we'll have to manually update the leases. We've chatted with Teri Dane and Mike Griffin of NCDMF about this and they've agreed to give us updates quarterly.

To mannually update the leases in the ShellCast SQL database, follow these steps.

1. Download the lease .shp file frim NCDMF to your local machine and save it (and all the associated .shp files) in the analysis > data > spatial > outputs > ncdmf_data > lease_bounds_raw directory as `lease_bounds_raw.shp`.
2. Run the `ncdmf_tidy_lease_data_script.R` either in the command line or in RStudio. This script will generate `lease_centroids_albers.shp` and `lease_bounds_albers.shp` in the shellcast repository. That is these files will be exported to the `lease_centroids` and `lease_bounds` directories, respectively, within the analysis > data > spatial > outputs > ncdmf_data directory.
3. The next day, the `gcp_update_mysqldb_script.py` script will check to see if there are new leases to be added to the SQL database. It will update them if there are and all other downstream analyses will be run normally with the newly updated leases.

## 8. Contact Information

If you have any questions, feedback, or suggestions please submit issues [through the NCSU Enterprise GitHub](https://github.ncsu.edu/biosystemsanalyticslab/shellcast/issues) or [through GitHub (public)](https://github.com/Biosystems-Analytics-Lab/shellcast/issues). You can also reach out to Sheila Saia (ssaia at ncsu dot edu) or Natalie Nelson (nnelson4 at ncsu dot edu).