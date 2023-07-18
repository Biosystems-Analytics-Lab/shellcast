# shellcast_analysis

### PQPF data
Source: NOAA
About PQPF:  https://www.wpc.ncep.noaa.gov/pqpf/about_pqpf_products.shtml
Data URL:  https://ftp.wpc.ncep.noaa.gov/pqpf/conus/

### Data ShellCast uses for analysis
**URL**:  https://ftp.wpc.ncep.noaa.gov/pqpf/conus/pqpf_24hr/
**Z run**: 06Z
**Interval**: 24 hours
**Data format**: GRIB
**Projection**: Lambert Conformal Conic 2SP
**Special resolution**: approx. 2.5km

**Data type**: Exceedance grids
**Data files**:

* pqpf_p24i_conus_{date}06f030.grb - 24 hour totals starting 12Z Monday and ending 12Z Tuesday (Day 1)
* pqpf_p24i_conus_{date}06f054.grb - 24 hour totals starting 12Z Tuesday and ending 12Z Wednesday (Day 2)
* pqpf_p24i_conus_{date}06f078.grb - 24 hour totals starting 12Z Wednesday and ending 12Z Thursday (Day 3)

**GRIB file content**:

- 0.25"   |Total_precipitation_surface_24_Hour_Accumulation_probability_above_6p35
- 0.5"     |Total_precipitation_surface_24_Hour_Accumulation_probability_above_12p7
- 1"        |Total_precipitation_surface_24_Hour_Accumulation_probability_above_25p4
- 1.5"     |Total_precipitation_surface_24_Hour_Accumulation_probability_above_38p1
- 2"        |Total_precipitation_surface_24_Hour_Accumulation_probability_above_50p8
- 2.5"     |Total_precipitation_surface_24_Hour_Accumulation_probability_above_63p5
- 3"        |Total_precipitation_surface_24_Hour_Accumulation_probability_above_76p2
- 4"        |Total_precipitation_surface_24_Hour_Accumulation_probability_above_101p6
- 5"        |Total_precipitation_surface_24_Hour_Accumulation_probability_above_127
- 6"        |Total_precipitation_surface_24_Hour_Accumulation_probability_above_152p4
- 8"        |Total_precipitation_surface_24_Hour_Accumulation_probability_above_203p2
- 16"      |Total_precipitation_surface_24_Hour_Accumulation_probability_above_406p4

**Notes**:

- NC thresholds (as of April 2023): 1.0, 1.5, 2.0, 2.5, 3.0, 4.0
- SC thresholds (as of April 2023): 4.0


### System Settings
#### Prerequisite
* MySQL database and database tables should be created before running ShellCast analysis.
* Create virtual environment.
  * Note: If you encountered "rasterio" installation problem with pip, try to use conda virtual environment.

* wgrib2 installed - wgrib2 is available for Linux/MacOS. Cygwin installation is required for Windows.
  * https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/
  * https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/compile_questions.html
  * https://www.ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/INSTALLING
  * https://ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/_README.cygwin
  * https://theweatherguy.net/blog/weather-links-info/how-to-install-and-compile-wgrib2-on-mac-os-10-14-6-mojave/

* GDAL installed - For windows [OSGEO4W](https://trac.osgeo.org/osgeo4w/) installation might be easiest. Set environment variable after successful OSGEO4W installation.  
  * https://gisforthought.com/setting-up-your-gdal-and-ogr-environmental-variables/

* gcloud CLI installed
  * https://cloud.google.com/sdk/docs/install

* Cloud SQL Auth proxy downloaded
  * https://cloud.google.com/sql/docs/mysql/sql-proxy

* Input data prepared

#### Optional tool
* Panoply to visualize GRIB file. https://www.giss.nasa.gov/tools/panoply/

### Analysis Settings

* Modify config_template.ini and rename it to config.ini
* Install Cloud SQL Proxy in analysis folder.  Follow steps [here](https://cloud.google.com/sql/docs/mysql/sql-proxy#windows-64-bit).
* (Windows only) Modify sqlauthproxy_template.bat and rename it to sqlauthproxy.bat.
* (Windows only) Set Task Scheduler to run ```analysis_run.bat```