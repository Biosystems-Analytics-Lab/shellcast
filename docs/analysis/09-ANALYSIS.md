# 9. Analysis background and compile reference

> **Doc 9 of 9** · [← 8. Troubleshooting](08-TROUBLESHOOTING.md) · [Index](README.md)

ShellCast analysis and setup are described in this file. The analysis includes North Carolina, South Carolina, and Florida as of May 2024. The outputs of the analysis are stored in the MySQL database of Google Cloud SQL. For information on how to set up the database, please refer to [DATABASE.md](../DATABASE.md).

> **Guides 1–8:** For onboarding, operations, configuration, notifications, and troubleshooting, follow the [numbered guides](README.md#reading-order) (`01-` … `08-`). This file retains background, data specifications, and GIS processing notes. **Tool installation** is in [01-GETTING_STARTED.md](01-GETTING_STARTED.md) §5–6.

## Table of Contents

0. [Background](#0-background)
1. [List of Acronyms](#1-list-of-acronyms)
2. [Description of Analysis Scripts](#2-description-of-analysis-scripts)
3. [Data](#3-data)
4. [Geospatial processing (GIS)](#4-geospatial-processing-gis)
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

#### Z time: why **06Z**, then why **`f030`**

ShellCast emails go out around **7 AM Eastern**. PQPF comes from NOAA/WPC. Two different times are easy to mix up:

| Clock | Z time | Eastern (typical) | Meaning |
|-------|--------|-------------------|---------|
| **When NOAA finishes the run** | **06Z** | **~1 AM EST** / **~2 AM EDT** | New PQPF GRIB files for today’s `{date}06…` cycle |
| **What counts as one forecast “rain day”** | **12Z → 12Z** | **~7 AM EST** / **~8 AM EDT** | Each 24-hour exceedance period in the product |

**06Z is not 7 AM.** They answer different questions.

**Why ShellCast uses the 06Z cycle**

The ShellCast analysis cron runs at **~6:40 AM Eastern** (see [05-DAILY_OPERATIONS.md](05-DAILY_OPERATIONS.md)). Subscribers get SMS around **7 AM Eastern**. ShellCast needs the **newest PQPF that is already on NOAA’s FTP** before that job runs.

On a typical morning:

```
~1 AM ET (06Z)       NOAA starts the PQPF run
~6:40 AM ET          Files on FTP; ShellCast cron downloads and runs analysis
~7:00 AM ET (≈12Z)   SMS / email to growers
```

**06Z is used because it is the latest NOAA run ready before the 7 AM product** — not because 06Z equals 7 AM. A **12Z run** (commented alternative in `constants.py`: `Z_RUN = '12'`, `f024` / `f048` / `f072`) would **start** at 7 AM and finish hours later, so it cannot feed a 7 AM email. ShellCast uses **06Z year-round** (winter and summer); only the Eastern wall-clock label changes (1 AM vs 2 AM).

Code: `Z_RUN = "06"` and filenames like `pqpf_p24i_conus_{YYYYMMDD}06f030.grb` in `analysis/shellcast-analysis/src/constants.py` and `pqpf_procs.py`.

**Why `f030` (and then `f054`, `f078`)**

The **`f` number is hours after the 06Z run**, not “24 hours of data.” Each file still holds **one 24-hour** probability product. NOAA defines those 24 hours on **12Z boundaries** (7 AM Eastern in standard time).

From **06Z**, the first full **12Z → 12Z** bucket ends **30 hours** later:

```
06Z run  +  30 h  =  12Z  →  first forecast day  →  f030  →  ShellCast pqpf_24h (Day 1)
06Z run  +  54 h  =  12Z  →  second day           →  f054  →  pqpf_48h (Day 2)
06Z run  +  78 h  =  12Z  →  third day            →  f078  →  pqpf_72h (Day 3)
```

Each step adds **24 hours** to the lead time (30, 54, 78). Code renames files with `TO_HOUR = -6` because **06Z + 6 h = 12Z**: `f030` → `30 + (−6)` = **24h**, and so on for 48h and 72h.

Example (run **Tuesday** morning, file date Tuesday, `…0606f030`):

| File | 24 h window (Z) | ShellCast day |
|------|-----------------|---------------|
| **f030** | 12Z Tue → 12Z Wed | Day 1 (“today”) |
| **f054** | 12Z Wed → 12Z Thu | Day 2 |
| **f078** | 12Z Thu → 12Z Fri | Day 3 |

Florida only crops **`f030`** (one email day); NC/SC use all three.

**Summer (EDT) note:** PQPF “rain days” stay fixed at **12Z–12Z UTC** (8 AM–8 AM Eastern during daylight saving). ShellCast still runs at **~6:40 / 7 AM Eastern** and still downloads the **06Z** cycle. XMRG (Florida observed rain) anchors at **7 AM Eastern local** — so in summer there is about a **one-hour** offset between XMRG’s anchor and PQPF’s 12Z buckets. That is a long-standing quirk of NOAA’s UTC-fixed product, not a reason to switch away from 06Z.

**One-line summary:** **06Z = when NOAA delivers the forecast (~1 AM ET); 12Z = what “today’s rain day” means in that forecast (~7 AM ET in winter).** ShellCast picks 06Z for timing and **`f030`** for the first 12Z–12Z day after that run.

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

## 4. Geospatial processing (GIS)

> **Install and environment setup** (Cloud SQL proxy, Python venv, Florida external tools via `setup-florida-dev.sh`): [01-GETTING_STARTED.md](01-GETTING_STARTED.md) §4–6. Florida needs wgrib2, `cnvgrib`, CDO, and GDAL (§6); NC/SC need wgrib2 for PQPF cropping (§5).

**Flowcharts and per-state comparison:** [03-STATE_GUIDES.md](03-STATE_GUIDES.md).

### 4.1 wgrib2 — PQPF crop (all states)

After NOAA PQPF GRIB2 files download to `data/pqpf/{state}/`, `pqpf_procs.py` calls **wgrib2** with `-small_grib` using `LON_WE` and `LAT_SN` from `analysis_settings.ini`. That keeps only the state's bounding box — smaller files, faster raster work. NC and SC then sample cropped grids at lease points and SHA means. Florida uses the same crop step for its single PQPF file (`f030` only).

### 4.2 Florida XMRG pipeline — observed multi-day rain

Florida closure rules depend on **how much rain has already fallen** over multi-day windows, not only PQPF exceedance probabilities. ShellCast builds **observed** totals from NOAA **XMRG** (hourly GRIB1, [§3.2](#32-daily-quality-controlled-rainfall-estimates-fl-only)), then combines with PQPF in `fl_pqpf.py`.

**End-to-end chain** (`fl_main.py` → `tp_xmrg.py` → `xmrg_proc.sh` → `fl_pqpf.py`):

| Step | Component | GIS role |
|------|-----------|----------|
| 1 | `tp_xmrg.py` | Download ~6 days of hourly `xmrg{MMDDYYYYHH}z.grb` into `data/tp/raw/` (aligned to 7:00 AM Eastern). |
| 2 | **`cnvgrib`** | Convert each GRIB1 file → GRIB2 under `data/tp/fl/intermediate/cnvgrib2/` (CDO/GDAL expect GRIB2). |
| 3 | **CDO `mergetime`** | Stack hourly GRIB2 into one multi-timestep series (oldest → newest). |
| 4 | **GDAL `gdalwarp`** | Reproject polar stereographic GRIB → WGS84. |
| 5 | **wgrib2 `-small_grib`** | Crop to Florida bounds (same idea as PQPF crop). |
| 6 | **CDO** (`copy`, `expr`, `setattribute`, `timcumsum`, `seltimestep`) | Build **running multi-hour totals** and extract maps at 24, 48, 72, 96, 120 h. |
| 7 | **GDAL** | Write `tp_24h.tif` … `tp_120h.tif` under `data/tp/fl/outputs/`. |
| 8 | `fl_pqpf.py` | Sample GeoTIFFs at lease/SHA points; compare to FDACS duration thresholds; merge with PQPF probability. |

#### Why CDO is required (concept)

XMRG is **one file per hour** — each file is rain in **that hour only**. Florida needs **cumulative** totals (e.g. sum of the last 48 hours at each grid cell). CDO's `timcumsum` walks the time axis:

| Hour (example) | Rain **this hour** | After **`timcumsum`** (running total) |
|----------------|----------------------|----------------------------------------|
| 1 | 0.10 in | 0.10 in |
| 2 | 0.05 in | 0.15 in |
| 3 | 0.20 in | 0.35 in |
| … | … | … |
| 24 | (hour 24 only) | **Sum of hours 1–24** → `tp_24h.tif` |

| `xmrg_proc.sh` command (concept) | Purpose |
|----------------------------------|---------|
| `cdo -mergetime …` | Combine hourly GRIB2 in `cnvgrib2/` into one multi-timestep file. |
| `cdo -f nc copy …` | GRIB → NetCDF for subsequent operators. |
| `cdo expr,…` | mm → inches (`× 0.03937`). |
| `cdo setattribute,…` | Set `units=inches` metadata. |
| `cdo timcumsum …` | Running sum from first hour through each timestep. |
| `cdo seltimestep,N …` | Grid at hour N (24, 48, 72, 96, 120) = **N-hour total**. |

Reprojection and geographic crop use **GDAL** and **wgrib2**, not CDO — see step table above.

## 5. CRON Job Set Up

See also [05-DAILY_OPERATIONS.md](05-DAILY_OPERATIONS.md) for a concise production checklist.

### 5.1 Executable Files

The cron job environment differs from the development environment. It is important that system be able to access files and directories as well as executable files in order to execute them. Run the following command in the terminal.

`chmod +x {path to bash script}`

- shellcast-analysis/analysis_run.sh
- analysis/shellcast-analysis/analysis_paths.sh
- shellcast-analysis/src/fl_pqpf/xmrg_proc.sh
- shellcast-analysis/ncep-lib-utils/nceplibs/bin/cnvgrib

**wgrib2 (system install, not the build tree):** after compiling, install the command as **`/usr/local/bin/wgrib2`**. ShellCast does not run `wgrib2/build/src/wgrib2` from the clone directory. On macOS, `pqpf_procs.py` calls `/usr/local/bin/wgrib2` explicitly; Florida `xmrg_proc.sh` expects `wgrib2` on `PATH` (it prepends `/usr/local/bin`). Use `./setup-florida-dev.sh` or see [01-GETTING_STARTED.md](01-GETTING_STARTED.md) §5.

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
