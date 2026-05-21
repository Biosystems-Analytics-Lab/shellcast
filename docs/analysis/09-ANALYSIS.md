# 9. Analysis background and compile reference

> **Doc 9 of 9** · [← 8. Troubleshooting](08-TROUBLESHOOTING.md) · [Index](README.md)

ShellCast analysis and setup are described in this file. The analysis includes North Carolina, South Carolina, and Florida as of May 2024. The outputs of the analysis are stored in the MySQL database of Google Cloud SQL. For information on how to set up the database, please refer to [DATABASE.md](../DATABASE.md).

> **Guides 1–8:** For onboarding, operations, configuration, notifications, and troubleshooting, follow the [numbered guides](README.md#reading-order) (`01-` … `08-`). This file retains background, data specifications, and detailed compile/setup notes.

## Table of Contents

0. [Background](#0-background)
1. [List of Acronyms](#1-list-of-acronyms)
2. [Description of Analysis Scripts](#2-description-of-analysis-scripts)
3. [Data](#3-data)
4. [Development Environment Set Up](#4-development-environment-set-up)
5. [CRON Job Set Up](#5-cron-job-set-up)
6. [Pushing Changes to GitHub](#6-pushing-changes-to-github)
7. [Updating Leases](#7-updating-leases)
8. [Contact Information](#8-contact-information)

## 0. Background

The main purpose of the scripts in the analysis folder is to: (1) pull Probabilistic Quantitative Precipitation
Forecasting (PQPF) data from a remote server at the NOAA, (2) do geospatial analysis based on given thresholds
determined by organizations, (3) classify step 2 values, and (4) update the ShellCast MySQL database. For a schematic
representation of this workflow, including how they relate to other major components of the ShellCast web application,
see the ShellCast [architecture overview](../../README.md#3-architecture-overview). The current ShellCast forecast is
for North Carolina, South Carolina, and Florida.

The analysis daily CRON job ensures that the three steps described above will run every day at 6:40 am ET on the
temporary project computer (iMac).

## 1. List of Acronyms

- North Carolina State University (NCSU)
- North Carolina Division of Marine Fisheries (NCDMF)
- North Carolina Department of Environmental Quality (NCDEQ)
- South Carolina Department of Health and Environmental Control (SCDHEC)
- Florida Department of Agriculture and Consumer Services (FDACS)
- National Oceanic and Atmospheric Administration (NOAA)
- Probabilistic Quantitative Precipitation Forecasting (PQPF)
- Google Cloud Platform (GCP)
- Climate Data Operators (CDO)
- Shellfish Harvested Area (SHA)
- Contiguous United States, and as the 48 contiguous states (CONUS)

## 2. Analysis and Scripts

### Preprocessing input data

ESRI ArcGIS Pro Modelbuilder was used to create the processing tools for each state. Assigning shellfish harvested area rainfall threshold to leases within the area, checking and fixing geometry, and assigning appropriate column names to attributes tables are among the tasks. The ArcGIS Pro project file is not included in the repository.

_Note_: Input data needs to be updated periodically. Currently, NCSU is responsible for updating input data. We may be able to automate updates if organizations publish shapefiles online in the data format we require.

### Analysis

**Requisites:**
_The MySQL Google Cloud SQL database, tables, and data need to be set up. please refer to [DATABASE.md](DATABASE.md) for more information._ </br>

Each state has its own geospatial analysis, however, North Carolina and Florida analysis share the same analogy; 1) finding the probability of precipitation from PQPF data for each lease location, 2) finding the mean value within the SHA area, 3) classifying the values into very low, low, moderate, high, and very high, and 4) saving categorized values to a remote MySQL database. Analysis for Florida adds complexity due to duration-based rainfall thresholds (e.g. 5 days > 3.5"). In addition to PQPF, daily quality controlled rainfall estimates are used to calculate rainfall accumulation.

In South Carolina analysis, SHA are considered lease areas. The mean PQPF for each SHA is calculated using geospatial statistics and follow step 3) and 4) as described above.

### Scripts

- `src`- all analysis code
  - `{state}_pqpf` - code for geospatial analysis specific to a state
  - `pqpf_procs.py` and `utils.py` - code for common processes
- `shellcast-analysis/{state}_main.py` - This script runs geospatial analysis and saves the output data to a remote MySQL server.
  - Prerequisites : create a virtual environment and connect to a remote MySQL server.
- `setup_logging.py` and `{state}_logging.yaml` - Logs file settings
- `analysis_settings.ini` - Python settings: databases, shapefile names, notification flags (read by `*_main.py` and `src/`).
- `analysis_paths.sh` - Shell-only paths: Cloud SQL proxy, venv, and `*_main.py` locations (sourced by `analysis_run.sh`).
- `analysis_run.sh` - This script is configured to run a cron job. The script activates the virtual environment, connects to the remote MySQL database, and runs `{state}_main.py`. Modifying this script file is recommended if you wish to run a state analysis only by commenting out the other states.

## 3. Data

### 3.1 PQPF data

**Source**: NOAA </br>
**About PQPF**: https://www.wpc.ncep.noaa.gov/pqpf/about_pqpf_products.shtml </br>
**Z run**: 06Z </br>
**Interval**: 24 hours </br>
**Data format**: Grib2 </br>
**Projection**: Lambert Conformal Conic 2SP </br>
**Special resolution**: approx. 2.5km </br>
**Data type**: Exceedance grids </br>
**Data files**: </br>

- pqpf*p24i_conus*{date}06f030.grb - 24 hour totals starting 12Z Monday and ending 12Z Tuesday (Day 1)
- pqpf*p24i_conus*{date}06f054.grb - 24 hour totals starting 12Z Tuesday and ending 12Z Wednesday (Day 2)
- pqpf*p24i_conus*{date}06f078.grb - 24 hour totals starting 12Z Wednesday and ending 12Z Thursday (Day 3)

**GRIB file content**:

- 0.25" |Total_precipitation_surface_24_Hour_Accumulation_probability_above_6p35
- 0.5" |Total_precipitation_surface_24_Hour_Accumulation_probability_above_12p7
- 1" |Total_precipitation_surface_24_Hour_Accumulation_probability_above_25p4
- 1.5" |Total_precipitation_surface_24_Hour_Accumulation_probability_above_38p1
- 2" |Total_precipitation_surface_24_Hour_Accumulation_probability_above_50p8
- 2.5" |Total_precipitation_surface_24_Hour_Accumulation_probability_above_63p5
- 3" |Total_precipitation_surface_24_Hour_Accumulation_probability_above_76p2
- 4" |Total_precipitation_surface_24_Hour_Accumulation_probability_above_101p6
- 5" |Total_precipitation_surface_24_Hour_Accumulation_probability_above_127
- 6" |Total_precipitation_surface_24_Hour_Accumulation_probability_above_152p4
- 8" |Total_precipitation_surface_24_Hour_Accumulation_probability_above_203p2
- 16" |Total_precipitation_surface_24_Hour_Accumulation_probability_above_406p4

**Notes**:

- NC thresholds (as of April 2024): 1.0, 1.5, 2.0, 2.5, 3.0, 4.0
- SC thresholds (as of April 2024): 4.0
- FL thresholds (as of April 2024):

### 3.2 Daily quality controlled rainfall estimates (FL only)

**Source**: NOAA </br>
**Interval**: Hourly </br>
**Format**: Grib1 </br>
**Projection**: Polar Stereographic </br>
**Special resolution**: approx. 4.7km </br>
**Data**: Total precipitation surface 1 Hour Accumulation </br>
**Data files**: xmrg{date}{utc}z.grb

### 3.3 Input Data

1. NC lease and SHA shapefiles (NCDEQ)
2. SC SHA shapefiles (SCDHEC)
3. FL lease and SHA shapefiles (FDACS)

## 4. Development Environment Set Up

### 4.1 Clone the ShellCast GitHub repository

Clone the GitHub repository to your machine by running

```bash
git clone https://github.com/Biosystems-Analytics-Lab/shellcast.git
```

### 4.2 Install and initialize Google Cloud SDK

The Google Cloud SDK is principally a command line tool that allows you to interact with Google Cloud from your local machine and perform various tasks. You can download, install, and initialize the Google Cloud SDK by following [these instructions](https://cloud.google.com/sdk/docs/quickstart).

### 4.3 Download Cloud SQL proxy

**Prerequisite**: MySQL need to be installed on your machine. If you don't have MySQL installed, download MySQL from [here](https://dev.mysql.com/downloads/mysql/).

Download and setup the Cloud SQL proxy by following [these instructions](https://cloud.google.com/sql/docs/mysql/quickstart-proxy-test#install-proxy).

```bash
cd {path to}/shellcast
curl -o cloud-sql-proxy {url to download the proxy}
chmod +x ./cloud-sql-proxy
```

TCP connection is used for connecting to the database. Run the following command to start the proxy.

```bash
./cloud-sql-proxy --port 3306 {instance name}
```

You can quit proxy by `Control + c`. It is recommended creating a bash file in the same directory including code below since you will be using it frequently.

```bash
#!/bin/sh
./cloud-sql-proxy --port 3306 {instance name}
```

To connect to Cloud SQL instance, `source ./{filename}.sh` in the terminal.

### 4.4 Setup Python virtual environment

Use environment management tool of your choice, however, Set the latest version of Python that has been tested with [pygrib](https://pypi.org/project/pygrib/) package.

### 4.5 Create analysis_settings.ini and analysis_paths.sh

ShellCast uses **two** local config files (see [02-CONFIGURATION.md](02-CONFIGURATION.md)):

| File | Purpose |
|------|---------|
| `analysis_settings.ini` | Python: DB credentials, per-state shapefile names, email/notification flags |
| `analysis_paths.sh` | Cron shell: proxy path, venv, paths to `nc_main.py` / `sc_main.py` / `fl_main.py` |

Create them from the templates:

```bash
cp analysis_settings.template.ini analysis_settings.ini
cp analysis_paths.template.sh analysis_paths.sh
```

Update `analysis_settings.ini` when fields, data names, or areas of interest change. Update `analysis_paths.sh` when install locations on the machine change.

### 4.6 Download and compile wgrib2

wgrib2 crops CONUS PQPF GRIB2 files to each state's area of interest (see `LON_WE` / `LAT_SN` in `analysis_settings.ini`).

**Upstream source:** NOAA-EMC maintains wgrib2 on GitHub:

- [NOAA-EMC/wgrib2](https://github.com/NOAA-EMC/wgrib2) — official repository (README, prerequisites, `cmake` install steps, releases)

For any new install or upgrade, follow that repository's README and release notes; prerequisites and build steps are maintained there and may change over time.

**ShellCast production note:** The analysis iMac was set up with a **wgrib2 build from the development period around 2023**. The links and compile notes below are **kept as historical project notes**. They may not match current NOAA-EMC releases, macOS versions, or your machine. Prefer the GitHub repo above for a new install; treat the following as optional background only.

#### Historical / alternate references (may be outdated)

- [CPC wgrib2 product page](https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/)
- [CPC compile questions](https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/compile_questions.html)
- [CPC INSTALLING notes](https://www.ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/INSTALLING)
- [theweatherguy — wgrib2 on macOS](https://theweatherguy.net/blog/how-to-install-and-compile-wgrib2-on-macos-monterey-ventura/) (Monterey/Ventura era; may not apply to current macOS)

A Fortran compiler and `gcc`/`gfortran` (e.g. `brew install gcc` on Mac) were required for older source builds.

#### Cron on macOS (project experience — verify for your setup)

`pqpf_procs.py` calls wgrib2 via **subprocess**. Under cron, wgrib2 sometimes failed to run until:

- **Full Disk Access** was enabled for Terminal — **System Settings** > **Privacy and Security** > **Full Disk Access**
- The **full path** to the `wgrib2` binary was used in code (not only `PATH`)
- Full Disk Access was granted to the calling environment if subprocess errors persisted

See also [08-TROUBLESHOOTING.md](08-TROUBLESHOOTING.md).

### 4.7 Download and Compile NCEPLIBS GRIB Utility and Dependencies (FL only)

Florida uses NOAA **XMRG** hourly total-precipitation files in **GRIB1** format (see [§3.2](#32-daily-quality-controlled-rainfall-estimates-fl-only)). After **`cnvgrib`** converts them to GRIB2, **`xmrg_proc.sh`** uses other tools to build multi-day rainfall totals: [CDO](#48-install-cdo-fl-only) (Climate Data Operators) for time-series merge and math on GRIB/NetCDF, GDAL for reprojection, **wgrib2** to crop to Florida, then GDAL again for GeoTIFF output. GRIB1→GRIB2 conversion is the first step and is done with **`cnvgrib`** from [NCEPLIBS-grib_util](https://github.com/NOAA-EMC/NCEPLIBS-grib_util).

#### How ShellCast uses `cnvgrib`

| Step | Component | Role |
|------|-----------|------|
| 1 | `fl_main.py` → `tp_xmrg.py` | Downloads `xmrg{MMDDYYYYHH}z.grb` from NOAA FTP into `data/tp/raw/` (about six days of hourly files, aligned to 7:00 AM Eastern). |
| 2 | `src/fl_pqpf/xmrg_proc.sh` | For every file in `data/tp/raw/`, runs `cnvgrib -g12 <input.grb> <output.grb>` and writes GRIB2 copies under `data/tp/fl/intermediate/cnvgrib2/`. Exits with an error if the GRIB1 and GRIB2 file counts do not match. |
| 3 | `xmrg_proc.sh` (continued) | See [§4.8](#48-install-cdo-fl-only): CDO merges hours and computes cumulative rain; GDAL reprojects; **wgrib2** crops; outputs `tp_24h.tif`, `tp_48h.tif`, … under `data/tp/fl/outputs/`. |
| 4 | `fl_pqpf.py` | Samples those GeoTIFFs at lease/SHA points (`tp_accum`), subtracts observed rain from FDACS thresholds, and picks the PQPF probability layer for the forecast. |

The script invokes the binary at `ncep-lib-utils/nceplibs/bin/cnvgrib` (see [§5.1](#51-executable-files) for cron `PATH` / full-path notes). ShellCast only requires **`cnvgrib`** from the grib_util package; other utilities in that repo can be omitted at compile time if they fail to build (see below).

#### Compile NCEPLIBS-grib_util

Clone `NCEPLIB-grib_util` from [NOAA-EMC GitHub](https://github.com/NOAA-EMC/NCEPLIBS-grib_util). The steps for compiling dependencies and utility can be found in `ncep-lib-utils/ncep_lib_utils.sh`. It is recommended that each dependency be compiled separately to ensure successful compilation. </br></br>
In the script you see `make -j4` which means that the compilation will be done in parallel using 4 threads. You can change the number of threads.
The rule of thumb seems to be `-j <number of cores>` or `-j <number of cores * 1.5>`. Increasing too high may result in slower performance.</br></br>
The third-party libraries `Jasper`, `libpng`, `zlib`, `BLAS`, and `LAPACK` must be installed before the dependencies are compiled.
On MacOS, you can install these dependencies using Homebrew: `brew install jasper`, `brew install libpng`, `brew install zlib`, and `brew install openblas`. The `openblas` installs both BLAS and LAPACK libraries. </br></br>

If you encounter compilation problems with tools other than the cnvgrib tool, you can disable compilation by commenting out tool names in ncep-lib-utils/NCEPLIBS-grib_util/src/CMakeLists.txt (e.g. # add_subdirectory(tocgrib)).

### 4.8 Install CDO (FL only)

**CDO** ([Climate Data Operators](https://code.mpimet.mpg.de/projects/cdo)) is a command-line toolkit for processing gridded climate and weather data (GRIB, NetCDF, and related formats). ShellCast does not call CDO from Python; `src/fl_pqpf/xmrg_proc.sh` invokes the `cdo` executable after `cnvgrib` has produced GRIB2 files.

#### Why Florida analysis needs CDO

XMRG provides **one GRIB file per hour**. Florida logic needs **cumulative rainfall over 24, 48, 72, 96, and 120 hours** at each grid cell (mapped to `tp_24h.tif`, … for lease/SHA sampling in `fl_pqpf.py`). CDO is used for the time-axis work that is awkward to do in Python alone:

| `xmrg_proc.sh` command (concept) | Purpose |
|----------------------------------|---------|
| `cdo -mergetime …` | Combine hourly GRIB2 files in `cnvgrib2/` into one multi-timestep file. |
| `cdo -f nc copy …` | Convert cropped GRIB to NetCDF for the next steps. |
| `cdo expr,…` | Convert 1-hour accumulation from millimeters to inches (`× 0.03937`). |
| `cdo setattribute,…` | Set the `units=inches` metadata on the variable. |
| `cdo timcumsum …` | Running sum over time → cumulative precipitation at each hour. |
| `cdo seltimestep,N …` | Pull out the timestep that equals **N hours** of accumulation (24, 48, …). |

Reprojection and cropping are **not** done by CDO in this script: **GDAL** (`gdalwarp`) reprojects polar stereographic GRIB to WGS84, and **wgrib2** (`-small_grib`) crops to the Florida bounding box before CDO works on the smaller grid.

#### Install

On macOS, a typical install is Homebrew: `brew install cdo`

Ensure `cdo` is on `PATH` when cron runs `xmrg_proc.sh` (the script prepends `/usr/local/bin`; see [§5.1](#51-executable-files) if cron reports `cdo: command not found`).

## 5. CRON Job Set Up

See also [05-DAILY_OPERATIONS.md](05-DAILY_OPERATIONS.md) for a concise production checklist.

### 5.1 Executable Files

The cron job environment differs from the development environment. It is important that system be able to access files and directories as well as executable files in order to execute them. Run the following command in the terminal.

`chmod +x {path to bash script}`

- shellcast-analysis/analysis_run.sh
- analysis/shellcast-analysis/analysis_paths.sh
- shellcast-analysis/src/fl_pqpf/xmrg_proc.sh
- shellcast-analysis/ncep-lib-utils/nceplibs/bin/cnvgrib

### 5.2 Terminal Permission

You need to give the terminal permission to run the script. On the Mac;

1. Go to **Settings** > **Security & Privacy**
2. Click on **Full Disk Access**
3. Search **Terminal** in the list and turn it on
   1. If you don't see **Terminal** in the list, click **+** sign at the bottom
   2. In **Privacy & Security** dialog, type in your **Password** > click **Modify Settings**
   3. In **Application** window, **Utilities** > **Terminal** > **Open**
   4. Search **Terminal** in the list and turn it on

### 5.2 Crontab Set Up

Tools for CRON jobs can be chosen freely by developers. Currently, ShellCast analyses are run on iMac computer using the `crontab` command.
`crontab -l` will list all the current cron jobs. To edit the cron jobs, run `crontab -e`.
It will open default text editor (e.g. nano, vi, vim, and etc) where you can add the following line to run the analysis every day at 6:40 am ET and save logs.
For example, your default editor is vi, type `i` to insert text, and then type the following line. After that, press `esc` and type `:wq` to save and exit.</br>
</br>
`40 6 * * * source {path to }/analysis_run.sh >> ~Desktop/cron.log 2>&1`

_Note that In **pqpf_procs.py**, **subprocess** is used to call **Wgrib2** to crop PQPF data. **Wgrib2** was unable to run when cron job was set. To work around this issue, the full path had to be included in the code._

### 5.3 File Permissions

If a cron job encounters an file permission issue, run the following code. `shellcast-analysys/data` directory may be prone to the issue since it stores data outputs.</br><br>
`chmod -R {permission numbers} {foldername or pathname}`
</br></br>
In case you are not familiar with permission numbers, you can learn from [RedHat's explanation of Linux file permissions](https://www.redhat.com/sysadmin/linux-file-permissions-explained). It is important to note that 777 is full permission, which raises security concerns. Any security concerns should be addressed with appropriate permissions.

## 6. Pushing Changes to GitHub

When appropriate, push changes to [github.com/Biosystems-Analytics-Lab/shellcast](https://github.com/Biosystems-Analytics-Lab/shellcast) as described in [GETTING_STARTED.md](../../GETTING_STARTED.md) (clone, pre-commit, and push workflow).

## 7. Updating Leases

Untill we're able to get REST API access from the North Carolina Division of Marine Fisheries (NCDMF), we'll have to manually update the leases. We've chatted with Teri Dane and Mike Griffin of NCDMF about this and they've agreed to give us updates quarterly.

To mannually update the leases in the ShellCast SQL database, follow these steps.

1. Download the lease .shp file frim NCDMF to your local machine and save it (and all the associated .shp files) in the analysis > data > spatial > outputs > ncdmf_data > lease_bounds_raw directory as `lease_bounds_raw.shp`.
2. Run the `ncdmf_tidy_lease_data_script.R` either in the command line or in RStudio. This script will generate `lease_centroids_albers.shp` and `lease_bounds_albers.shp` in the shellcast repository. That is these files will be exported to the `lease_centroids` and `lease_bounds` directories, respectively, within the analysis > data > spatial > outputs > ncdmf_data directory.
3. The next day, the `gcp_update_mysqldb_script.py` script will check to see if there are new leases to be added to the SQL database. It will update them if there are and all other downstream analyses will be run normally with the newly updated leases.

## 8. Contact Information

If you have any questions, feedback, or suggestions please submit [GitHub issues](https://github.com/Biosystems-Analytics-Lab/shellcast/issues). You can also reach out to Sheila Saia (ssaia at ncsu dot edu) or Natalie Nelson (nnelson4 at ncsu dot edu).
