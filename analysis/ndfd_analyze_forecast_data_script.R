# ---- script header ----
# script name: ndfd_analyze_forecast_data_script.R
# purpose of script: takes raw ndfd tabular data and calculates probability of closure
# author: sheila saia
# date created: 20200525
# email: ssaia@ncsu.edu


# ---- notes ----
# notes:


# ---- to do ----
# to do list

# TODO include error message/script stopping for no recent data to pull
# TODO (wishlist) use here package
# TODO (wishlist) use terra package for raster stuff

# TODO remove notification testing factor (to bump up prob of closure values for testing)
notification_factor <- 3
notification_flag <- "testing" # or "production"


# ---- 1. install and load packages as necessary ----
# packages
packages <- c("tidyverse", "raster", "sf", "lubridate")

# install and load
for (package in packages) {
   if (! package %in% installed.packages()) {
     install.packages(package, dependencies = TRUE)
   }
  library(package, character.only = TRUE)
}


# ---- 2. define base paths ----
# base path to data
# data_base_path = "/home/ssaia/shellcast/analysis/data/" # set this and uncomment!
# data_base_path = "/Users/sheila/Documents/bae_shellcast_project/shellcast_analysis/web_app_data/"
data_base_path = "/Users/sheila/Documents/github_ncsu/shellcast/analysis/data/"

# ---- 3. use base paths and define projections ----
# path to ndfd spatial inputs
ndfd_spatial_data_input_path <- paste0(data_base_path, "spatial/outputs/ndfd_sco_data/")

# path to sga buffer spatial inputs
sga_spatial_data_input_path <- paste0(data_base_path, "spatial/inputs/ncdmf_data/sga_bounds/")

# path to cmu bounds spatial inputs
cmu_spatial_data_input_path <- paste0(data_base_path, "spatial/inputs/ncdmf_data/cmu_bounds/")

# path to lease bounds spatial inputs
lease_spatial_data_input_path <- paste0(data_base_path, "spatial/outputs/ncdmf_data/lease_bounds/")

# path to rainfall threshold tabular inputs
rainfall_thresh_tabular_data_input_path <- paste0(data_base_path, "tabular/inputs/ncdmf_rainfall_thresholds/")


# path to ndfd spatial outputs
ndfd_spatial_data_output_path <- paste0(data_base_path, "spatial/outputs/ndfd_sco_data/")

# path to ndfd tabular outputs
ndfd_tabular_data_output_path <- paste0(data_base_path, "tabular/outputs/ndfd_sco_data/")

# path to ignored lease bounds spatial outputs
lease_spatial_data_output_path <- paste0(data_base_path, "spatial/outputs/ncdmf_data/lease_bounds_ignored/")

# path to ignored lease bounds tabular outputs
lease_tabular_data_output_path <- paste0(data_base_path, "tabular/outputs/ndfd_sco_data/lease_calcs/leases_ignored/")

# path to ndfd tabular outputs appended
ndfd_tabular_data_appended_output_path <- paste0(data_base_path, "tabular/outputs/ndfd_sco_data_appended/")


# define proj4 string for ndfd data
ndfd_proj4 = "+proj=lcc +lat_1=25 +lat_2=25 +lat_0=25 +lon_0=-95 +x_0=0 +y_0=0 +a=6371000 +b=6371000 +units=m +no_defs"
# source: https://spatialreference.org/ref/sr-org/6825/

# define epsg and proj4 for N. America Albers projection (projecting to this)
na_albers_proj4 <- "+proj=aea +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs"
na_albers_epsg <- 102008

# define wgs 84 projection
wgs84_epsg <- 4326
wgs84_proj4 <- "+proj=longlat +datum=WGS84 +no_defs"


# ---- 4. pull latest ndfd file name (with date) ----
# list files in ndfd_sco_data_raw
# ndfd_files <- list.files(ndfd_spatial_data_input_path, pattern = "pop12_*") # if there is a pop12 dataset there's a qpf dataset

# find files with 24 hr data (just need one time period to check dates)
# ndfd_files_sel <- ndfd_files[stringr::str_detect(ndfd_files, "_24hr_nc_albers")]

# pull out dates
# ndfd_file_dates_str <- gsub("pop12_", "", gsub("00_24hr_nc_albers.tif", "", ndfd_files_sel)) # assumes midnight

# convert date strings to dates
# ndfd_file_dates <- lubridate::ymd(ndfd_file_dates_str)

# get today's date
# today_date_uct <- lubridate::today(tzone = "UCT")

# calcualte difference
# diff_ndfd_file_dates <- as.numeric(today_date_uct - ndfd_file_dates) # in days

# find position of smallest difference
# latest_ndfd_date_uct <- ndfd_file_dates[diff_ndfd_file_dates == min(diff_ndfd_file_dates)]

# convert to string
# latest_ndfd_date_uct_str <- strftime(latest_ndfd_date_uct, format = "%Y%m%d%H") # assumes midnight

# need some sort of error statement if this is more than a certain number of days then don't run script


# ---- 5. pull latest lease file name (with dates) ----
# list files in lease_bounds
# lease_files <- list.files(lease_spatial_data_input_path, pattern = "*.shp") # if there is a pop12 dataset there's a qpf dataset
# lease_files <- c(lease_files, "leases_20200401.shp") # to test with multiple

# pull out date strings
# lease_file_dates_str <- gsub("leases_albers_", "", gsub(".shp", "", lease_files))

# convert date strings to dates
# lease_file_dates <- lubridate::ymd(lease_file_dates_str)

# get today's date
# today_date_uct <- lubridate::today(tzone = "UCT")

# calcualte difference
# diff_lease_file_dates <- as.numeric(today_date_uct - lease_file_dates) # in days

# find position of smallest difference
# latest_lease_date_uct <- lease_file_dates[diff_lease_file_dates == min(diff_lease_file_dates)]

# convert to string
# latest_lease_date_uct_str <- strftime(latest_lease_date_uct, format = "%Y%m%d")

# need some sort of error statement if this is more than a certain number of days then don't run script


# ---- 6. load other data ----
# raster data
# latest pop12 ndfd data raster for 1-day, 2-day, and 3-day forecasts
# ndfd_pop12_raster_1day_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "pop12_", latest_ndfd_date_uct_str, "_24hr_nc_albers.tif")) # includes date in file name
# ndfd_pop12_raster_2day_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "pop12_", latest_ndfd_date_uct_str, "_48hr_nc_albers.tif")) # includes date in file name
# ndfd_pop12_raster_3day_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "pop12_", latest_ndfd_date_uct_str, "_72hr_nc_albers.tif")) # includes date in file name
ndfd_pop12_raster_1day_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "pop12_24hr_nc_albers.tif"))
ndfd_pop12_raster_2day_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "pop12_48hr_nc_albers.tif"))
ndfd_pop12_raster_3day_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "pop12_72hr_nc_albers.tif"))

# check projection
# crs(ndfd_pop12_raster_1day_albers)
# crs(ndfd_pop12_raster_2day_albers)
# crs(ndfd_pop12_raster_3day_albers)

# latest qpf ndfd data raster for 1-day, 2-day, and 3-day forecasts
# ndfd_qpf_raster_1day_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "qpf_", latest_ndfd_date_uct_str, "_24hr_nc_albers.tif")) # includes date in file name
# ndfd_qpf_raster_2day_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "qpf_", latest_ndfd_date_uct_str, "_48hr_nc_albers.tif")) # includes date in file name
# ndfd_qpf_raster_3day_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "qpf_", latest_ndfd_date_uct_str, "_72hr_nc_albers.tif")) # includes date in file name
ndfd_qpf_raster_1day_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "qpf_24hr_nc_albers.tif")) # includes date in file name
ndfd_qpf_raster_2day_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "qpf_48hr_nc_albers.tif")) # includes date in file name
ndfd_qpf_raster_3day_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "qpf_72hr_nc_albers.tif")) # includes date in file name

# check projection
# crs(ndfd_qpf_raster_1day_albers)
# crs(ndfd_qpf_raster_2day_albers)
# crs(ndfd_qpf_raster_3day_albers)

# spatial data
# sga buffer bounds
sga_buffer_albers <- st_read(paste0(sga_spatial_data_input_path, "sga_bounds_10kmbuf_albers.shp"))  %>%
  st_set_crs(na_albers_epsg) # epsg code wasn't assigned if this code isn't included

# sga data
sga_bounds_albers <- st_read(paste0(sga_spatial_data_input_path, "sga_bounds_simple_albers.shp"))  %>%
  st_set_crs(na_albers_epsg) # epsg code wasn't assigned if this code isn't included

# cmu buffer bounds
cmu_buffer_albers <- st_read(paste0(cmu_spatial_data_input_path, "cmu_bounds_10kmbuf_albers.shp"))  %>%
  st_set_crs(na_albers_epsg) # epsg code wasn't assigned if this code isn't included

# cmu bounds
cmu_bounds_albers <- st_read(paste0(cmu_spatial_data_input_path, "cmu_bounds_albers.shp"))  %>%
  st_set_crs(na_albers_epsg) # epsg code wasn't assigned if this code isn't included

# lease bounds
# use latest date to read in most recent data
# lease_data_albers <- st_read(paste0(lease_spatial_data_input_path, "leases_albers_", latest_lease_date_uct_str, ".shp")) %>%
#   st_set_crs(na_albers_epsg) # epsg code wasn't assigned if this code isn't included, includes date in file name
lease_data_albers <- st_read(paste0(lease_spatial_data_input_path, "lease_bounds_albers.shp")) %>%
  st_set_crs(na_albers_epsg) # epsg code wasn't assigned if this code isn't included

# check crs
# st_crs(sga_buffer_albers)
# st_crs(sga_bounds_albers)
# st_crs(cmu_buffer_albers)
# st_crs(cmu_bounds_albers)
# st_crs(lease_data_albers)

# tabular data
# rainfall thresholds
rainfall_thresh_data <- read_csv(paste0(rainfall_thresh_tabular_data_input_path, "rainfall_thresholds.csv"))


# ---- 7. crop nc raster ndfd data to sga bounds ----
# pop12 for 1-day, 2-day, and 3-day forecasts
ndfd_pop12_raster_1day_sga_albers <- raster::crop(ndfd_pop12_raster_1day_albers, sga_buffer_albers)
ndfd_pop12_raster_2day_sga_albers <- raster::crop(ndfd_pop12_raster_2day_albers, sga_buffer_albers)
ndfd_pop12_raster_3day_sga_albers <- raster::crop(ndfd_pop12_raster_3day_albers, sga_buffer_albers)

# plot to check
# plot(ndfd_pop12_raster_1day_sga_albers)
# plot(ndfd_pop12_raster_2day_sga_albers)
# plot(ndfd_pop12_raster_3day_sga_albers)

# qpf for 1-day, 2-day, and 3-day forecasts
ndfd_qpf_raster_1day_sga_albers <- raster::crop(ndfd_qpf_raster_1day_albers, sga_buffer_albers)
ndfd_qpf_raster_2day_sga_albers <- raster::crop(ndfd_qpf_raster_2day_albers, sga_buffer_albers)
ndfd_qpf_raster_3day_sga_albers <- raster::crop(ndfd_qpf_raster_3day_albers, sga_buffer_albers)

# plot to check
# plot(ndfd_qpf_raster_1day_sga_albers)
# plot(ndfd_qpf_raster_2day_sga_albers)
# plot(ndfd_qpf_raster_3day_sga_albers)

# project pop12 to wgs84 toofor 1-day, 2-day, and 3-day forecasts
# ndfd_pop12_raster_1day_sga_wgs84 <- projectRaster(ndfd_pop12_raster_1day_sga_albers, crs = wgs84_proj4)
# ndfd_pop12_raster_2day_sga_wgs84 <- projectRaster(ndfd_pop12_raster_2day_sga_albers, crs = wgs84_proj4)
# ndfd_pop12_raster_3day_sga_wgs84 <- projectRaster(ndfd_pop12_raster_3day_sga_albers, crs = wgs84_proj4)

# project qpf to wgs84 too for 1-day, 2-day, and 3-day forecasts
# ndfd_qpf_raster_1day_sga_wgs84 <- projectRaster(ndfd_qpf_raster_1day_sga_albers, crs = wgs84_proj4)
# ndfd_qpf_raster_2day_sga_wgs84 <- projectRaster(ndfd_qpf_raster_2day_sga_albers, crs = wgs84_proj4)
# ndfd_qpf_raster_3day_sga_wgs84 <- projectRaster(ndfd_qpf_raster_3day_sga_albers, crs = wgs84_proj4)

# plot to check
# plot(ndfd_pop12_raster_1day_sga_wgs84)
# plot(ndfd_qpf_raster_1day_sga_wgs84)
# plot(ndfd_pop12_raster_2day_sga_wgs84)
# plot(ndfd_qpf_raster_3day_sga_wgs84)
# plot(ndfd_pop12_raster_3day_sga_wgs84)
# plot(ndfd_qpf_raster_3day_sga_wgs84)


# ---- 8. export sga raster ndfd data ----
# export pop12 rasters for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_pop12_raster_1day_sga_albers, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct, "_24hr_sga_albers.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_2day_sga_albers, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct, "_48hr_sga_albers.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_3day_sga_albers, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct, "_78hr_sga_albers.tif"), overwrite = TRUE)

# export qpf rasters for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_qpf_raster_1day_sga_albers, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct, "_24hr_sga_albers.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_2day_sga_albers, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct, "_48hr_sga_albers.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_3day_sga_albers, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct, "_72hr_sga_albers.tif"), overwrite = TRUE)

# export pop12 rasters as wgs84 too for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_pop12_raster_1day_sga_wgs84, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct, "_24hr_sga_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_2day_sga_wgs84, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct, "_48hr_sga_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_3day_sga_wgs84, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct, "_78hr_sga_wgs84.tif"), overwrite = TRUE)

# export qpf rasters as wgs84 too for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_qpf_raster_1day_sga_wgs84, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct, "_24hr_sga_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_2day_sga_wgs84, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct, "_48hr_sga_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_3day_sga_wgs84, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct, "_72hr_sga_wgs84.tif"), overwrite = TRUE)


# ---- 9. crop sga raster ndfd data to cmu bounds ----
# 1-day pop12 for 1-day, 2-day, and 3-day forecasts
ndfd_pop12_raster_1day_cmu_albers <- raster::mask(ndfd_pop12_raster_1day_sga_albers, mask = cmu_buffer_albers)
ndfd_pop12_raster_2day_cmu_albers <- raster::mask(ndfd_pop12_raster_2day_sga_albers, mask = cmu_buffer_albers)
ndfd_pop12_raster_3day_cmu_albers <- raster::mask(ndfd_pop12_raster_3day_sga_albers, mask = cmu_buffer_albers)

# plot to check
# plot(ndfd_pop12_raster_1day_cmu_albers)
# plot(ndfd_pop12_raster_2day_cmu_albers)
# plot(ndfd_pop12_raster_3day_cmu_albers)

# 1-day qpf for 1-day, 2-day, and 3-day forecasts
ndfd_qpf_raster_1day_cmu_albers <-  raster::mask(ndfd_qpf_raster_1day_sga_albers, mask = cmu_buffer_albers)
ndfd_qpf_raster_2day_cmu_albers <-  raster::mask(ndfd_qpf_raster_2day_sga_albers, mask = cmu_buffer_albers)
ndfd_qpf_raster_3day_cmu_albers <-  raster::mask(ndfd_qpf_raster_3day_sga_albers, mask = cmu_buffer_albers)

# plot to check
# plot(ndfd_qpf_raster_1day_cmu_albers)
# plot(ndfd_qpf_raster_2day_cmu_albers)
# plot(ndfd_qpf_raster_3day_cmu_albers)

# project pop12 to wgs84 too for 1-day, 2-day, and 3-day forecasts
# ndfd_pop12_raster_1day_cmu_wgs84 <- projectRaster(ndfd_pop12_raster_1day_cmu_albers, crs = wgs84_proj4)
# ndfd_pop12_raster_2day_cmu_wgs84 <- projectRaster(ndfd_pop12_raster_2day_cmu_albers, crs = wgs84_proj4)
# ndfd_pop12_raster_3day_cmu_wgs84 <- projectRaster(ndfd_pop12_raster_3day_cmu_albers, crs = wgs84_proj4)

# project qpf to wgs84 too for 1-day, 2-day, and 3-day forecasts
# ndfd_qpf_raster_1day_cmu_wgs84 <- projectRaster(ndfd_qpf_raster_1day_cmu_albers, crs = wgs84_proj4)
# ndfd_qpf_raster_2day_cmu_wgs84 <- projectRaster(ndfd_qpf_raster_2day_cmu_albers, crs = wgs84_proj4)
# ndfd_qpf_raster_3day_cmu_wgs84 <- projectRaster(ndfd_qpf_raster_3day_cmu_albers, crs = wgs84_proj4)

# plot to check
# plot(ndfd_pop12_raster_1day_cmu_wgs84)
# plot(ndfd_pop12_raster_2day_cmu_wgs84)
# plot(ndfd_pop12_raster_3day_cmu_wgs84)
# plot(ndfd_qpf_raster_1day_cmu_wgs84)
# plot(ndfd_qpf_raster_2day_cmu_wgs84)
# plot(ndfd_qpf_raster_3day_cmu_wgs84)


# ---- 10. export cmu raster ndfd data ----
# export pop12 rasters for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_pop12_raster_1day_cmu_albers, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct, "_24hr_cmu_albers.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_2day_cmu_albers, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct, "_48hr_cmu_albers.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_3day_cmu_albers, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct, "_78hr_cmu_albers.tif"), overwrite = TRUE)

# export qpf rasters for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_qpf_raster_1day_cmu_albers, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct, "_24hr_cmu_albers.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_2day_cmu_albers, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct, "_48hr_cmu_albers.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_3day_cmu_albers, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct, "_72hr_cmu_albers.tif"), overwrite = TRUE)

# export pop12 rasters as wgs84 too for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_pop12_raster_1day_cmu_wgs84, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct, "_24hr_cmu_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_2day_cmu_wgs84, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct, "_48hr_cmu_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_3day_cmu_wgs84, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct, "_78hr_cmu_wgs84.tif"), overwrite = TRUE)

# export qpf rasters as wgs84 too for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_qpf_raster_1day_cmu_wgs84, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct, "_24hr_cmu_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_2day_cmu_wgs84, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct, "_48hr_cmu_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_3day_cmu_wgs84, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct, "_72hr_cmu_wgs84.tif"), overwrite = TRUE)


# ---- 11. area weighted ndfd cmu calcs ----
# need to do this for pop12 and qpf and for 1-day, 2-day, and 3-day forecasts
ndfd_cmu_calcs_data <- data.frame(row_num = as.numeric(),
                                  HA_CLASS = as.character(),
                                  rainfall_thresh_in = as.numeric(),
                                  datetime_uct = as.character(),
                                  valid_period_hrs = as.numeric(),
                                  pop12_perc = as.numeric(),
                                  qpf_in = as.numeric(),
                                  prob_close_perc = as.numeric())

# valid period list
valid_period_list <- c(24, 48, 72)

# define date
ndfd_date_uct <- lubridate::today(tzone = "UCT")

# rasters lists
pop12_cmu_raster_list <- c(ndfd_pop12_raster_1day_cmu_albers, ndfd_pop12_raster_2day_cmu_albers, ndfd_pop12_raster_3day_cmu_albers)
qpf_cmu_raster_list <- c(ndfd_qpf_raster_1day_cmu_albers, ndfd_qpf_raster_2day_cmu_albers, ndfd_qpf_raster_3day_cmu_albers)

# number of cmu's
num_cmu <- length(cmu_bounds_albers$HA_CLASS)

# row dimentions
num_cmu_row <- length(valid_period_list)*num_cmu

# set row number and start iterator
cmu_row_num_list <- seq(1:num_cmu_row)
cmu_row_num <- cmu_row_num_list[1]

# record start time
start_time <- now()

# for loop
# i denotes valid period (3 values), j denotes HA_CLASS (145 values)
for (i in 1:length(valid_period_list)) {
  for (j in 1:num_cmu) {
    # valid period
    temp_valid_period <- valid_period_list[i]

    # save raster
    temp_pop12_raster <- pop12_cmu_raster_list[i][[1]]
    temp_qpf_raster <- qpf_cmu_raster_list[i][[1]]

    # save raster resolution
    temp_pop12_raster_res <- raster::res(temp_pop12_raster)
    temp_qpf_raster_res <- raster::res(temp_qpf_raster)

    # save cmu name
    temp_cmu_name <- as.character(cmu_bounds_albers$HA_CLASS[j])

    # save cmu rainfall threshold value
    temp_cmu_rain_in <- as.numeric(cmu_bounds_albers$rain_in[j])

    # get cmu bounds vector
    temp_cmu_bounds <- cmu_bounds_albers %>%
      dplyr::filter(HA_CLASS == temp_cmu_name)

    # cmu bounds area
    temp_cmu_area <- as.numeric(st_area(temp_cmu_bounds)) # in m^2

    # make this a funciton that takes ndfd raster and temp_cmu_bounds and gives area wtd raster result
    # pop12
    temp_pop12_cmu_raster_empty <- raster()
    raster::extent(temp_pop12_cmu_raster_empty) <- raster::extent(temp_pop12_raster)
    raster::res(temp_pop12_cmu_raster_empty) <- raster::res(temp_pop12_raster)
    raster::crs(temp_pop12_cmu_raster_empty) <- raster::crs(temp_pop12_raster)

    #qpf
    temp_qpf_cmu_raster_empty <- raster()
    raster::extent(temp_qpf_cmu_raster_empty) <- raster::extent(temp_qpf_raster)
    raster::res(temp_qpf_cmu_raster_empty) <- raster::res(temp_qpf_raster)
    raster::crs(temp_qpf_cmu_raster_empty) <- raster::crs(temp_qpf_raster)

    # calculate percent cover cmu over raster
    temp_pop12_cmu_raster_perc_cover <- raster::rasterize(temp_cmu_bounds, temp_pop12_cmu_raster_empty, getCover = TRUE) # getCover give percentage of the cover of the cmu boundary in the raster
    temp_qpf_cmu_raster_perc_cover <- raster::rasterize(temp_cmu_bounds, temp_qpf_cmu_raster_empty, getCover = TRUE) # getCover give percentage of the cover of the cmu boundary in the raster

    # define percent cover values
    # every once in a while randomly get the error: "Error in data.frame(perc_cover = temp_pop12_cmu_raster_perc_cover@data@values,: arguments imply differing number of rows: 0, 3933"
    # not sure how stable the rasterize getCover option is (which might be the issue here, watch fasterize for updates but right now no ability to get percent cover)
    temp_pop12_perc_cov_values <- as.numeric(temp_pop12_cmu_raster_perc_cover@data@values)
    temp_qpf_perc_cov_values <- as.numeric(temp_qpf_cmu_raster_perc_cover@data@values)

    # define raster values
    # every once in a while randomly get the error: "Error in data.frame(perc_cover = temp_pop12_cmu_raster_perc_cover@data@values,: arguments imply differing number of rows: 0, 3933"
    # not sure how stable the rasterize getCover option is (which might be the issue here, watch fasterize for updates but right now no ability to get percent cover)
    temp_pop12_raster_values <- as.numeric(temp_pop12_raster@data@values)
    temp_qpf_raster_values <- as.numeric(temp_qpf_raster@data@values)

    # convert raster to dataframe
    temp_pop12_cmu_df <- data.frame(perc_cover = temp_pop12_perc_cov_values,
                                    raster_value = temp_pop12_raster_values)
    temp_qpf_cmu_df <- data.frame(perc_cover = temp_qpf_perc_cov_values,
                                  raster_value = temp_qpf_raster_values)

    # keep only dataframe entries with values and do spatial averaging calcs
    # pop12
    temp_pop12_cmu_df_short <- temp_pop12_cmu_df %>%
      na.omit() %>%
      dplyr::mutate(flag = if_else(perc_cover == 0, "no_data", "data")) %>%
      dplyr::filter(flag == "data") %>%
      dplyr::select(-flag) %>%
      dplyr::mutate(cmu_raster_area_m2 = perc_cover*(temp_qpf_raster_res[1]*temp_qpf_raster_res[2]))

    # qpf
    temp_qpf_cmu_df_short <- temp_qpf_cmu_df %>%
      na.omit() %>%
      dplyr::mutate(flag = if_else(perc_cover == 0, "no_data", "data")) %>%
      dplyr::filter(flag == "data") %>%
      dplyr::select(-flag) %>%
      dplyr::mutate(cmu_raster_area_m2 = perc_cover*(temp_qpf_raster_res[1]*temp_qpf_raster_res[2]))

    # find total area of raster represented
    temp_pop12_cmu_raster_area_sum_m2 = sum(temp_qpf_cmu_df_short$cmu_raster_area_m2)
    temp_qpf_cmu_raster_area_sum_m2 = sum(temp_qpf_cmu_df_short$cmu_raster_area_m2)

    # use total area to calculated weighted value
    temp_pop12_cmu_df_fin <- temp_pop12_cmu_df_short %>%
      dplyr::mutate(cmu_raster_area_perc = cmu_raster_area_m2/temp_pop12_cmu_raster_area_sum_m2,
                    raster_value_wtd = cmu_raster_area_perc * raster_value)
    temp_qpf_cmu_df_fin <- temp_qpf_cmu_df_short %>%
      dplyr::mutate(cmu_raster_area_perc = cmu_raster_area_m2/temp_qpf_cmu_raster_area_sum_m2,
                    raster_value_wtd = cmu_raster_area_perc * raster_value)

    # sum weighted values to get result
    temp_cmu_pop12_result <- round(sum(temp_pop12_cmu_df_fin$raster_value_wtd), 2)
    temp_cmu_qpf_result <- round(sum(temp_qpf_cmu_df_fin$raster_value_wtd), 2)

    # calculate probability of closure
    temp_cmu_prob_close_result <- round((temp_cmu_pop12_result * exp(-temp_cmu_rain_in/temp_cmu_qpf_result)), 1) # from equation 1 in proposal
    temp_cum_prob_closure_notification_test_result <- if_else(temp_cmu_prob_close_result * notification_factor > 100, 100, temp_cmu_prob_close_result * notification_factor) # to test notifications

    # save data
    temp_ndfd_cmu_calcs_data <- data.frame(row_num = cmu_row_num,
                                           HA_CLASS = temp_cmu_name,
                                           rainfall_thresh_in = temp_cmu_rain_in,
                                           datetime_uct = ndfd_date_uct,
                                           valid_period_hrs = temp_valid_period,
                                           pop12_perc = temp_cmu_pop12_result,
                                           qpf_in = temp_cmu_qpf_result,
                                           #prob_close_perc = temp_cmu_prob_close_result)
                                           prob_close_perc = temp_cum_prob_closure_notification_test_result) # to test notifications

    # bind results
    ndfd_cmu_calcs_data <-  rbind(ndfd_cmu_calcs_data, temp_ndfd_cmu_calcs_data)

    # next row
    print(paste0("finished row: ", cmu_row_num))
    cmu_row_num <- cmu_row_num + 1
  }
}

# print time now
stop_time <- now()

# time to run loop
stop_time - start_time
# Time difference of ~3 to 4 min

# print date
print(paste0(ndfd_date_uct, " spatial averaging complete"))


# ---- 12. export area weighted ndfd cmu calcs ----
# export calcs for 1-day, 2-day, and 3-day forecasts
# write_csv(ndfd_cmu_calcs_data, paste0(ndfd_tabular_data_output_path, "cmu_calcs/ndfd_cmu_calcs_", latest_ndfd_date_uct_str, ".csv")) # includes date in file name
write_csv(ndfd_cmu_calcs_data, paste0(ndfd_tabular_data_output_path, "cmu_calcs/ndfd_cmu_calcs.csv"))


# ---- 13. min and max ndfd sga calcs ----
# use rainfall threshold data to create a lookup table
cmu_sga_lookup <- rainfall_thresh_data %>%
  dplyr::select(HA_CLASS, grow_area)

# full sga list
sga_full_list <- st_drop_geometry(sga_bounds_albers) %>%
  dplyr::select(grow_area) %>%
  dplyr::distinct()

# join lookup table with cmu calcs
ndfd_cmu_calcs_join_data <- ndfd_cmu_calcs_data %>%
  dplyr::left_join(cmu_sga_lookup, by = "HA_CLASS")

# see how many sga's we have now
# length(unique(ndfd_cmu_calcs_data$HA_CLASS)) # 144
# length(unique(sga_bounds_albers$grow_area)) # 73
# length(unique(rainfall_thresh_data$grow_area)) # 48
# length(unique(ndfd_cmu_calcs_join_data$grow_area)) # 48
# there are 73-48 = 25 sga without cmus inside

# min and max calcs for each sga
ndfd_sga_calcs_data <- ndfd_cmu_calcs_join_data %>%
  dplyr::group_by(grow_area, valid_period_hrs) %>%
  dplyr::summarize(min = round(min(prob_close_perc), 0),
            max = round(max(prob_close_perc), 0)) %>%
  dplyr::mutate(valid_period_hrs = case_when(valid_period_hrs == 24 ~ "1d_prob",
                                             valid_period_hrs == 48 ~ "2d_prob",
                                             valid_period_hrs == 72 ~ "3d_prob")) %>%
  tidyr::pivot_wider(id_cols = "grow_area", names_from = valid_period_hrs, values_from = c(min, max)) %>%
  dplyr::right_join(sga_full_list, by = "grow_area") %>% # fills in missing sgas
  dplyr::select(grow_area_name = grow_area, min_1d_prob, max_1d_prob, min_2d_prob, max_2d_prob, min_3d_prob, max_3d_prob)

# ---- 14. export min and max ndfd sga calcs ----
# export sga min and max calcs for 1-day, 2-day, and 3-day forecasts
# write_csv(ndfd_sga_calcs_data,  paste0(ndfd_tabular_data_output_path, "sga_calcs/ndfd_sga_calcs_", latest_ndfd_date_uct_str, ".csv")) # includes date in file name
write_csv(ndfd_sga_calcs_data, paste0(ndfd_tabular_data_output_path, "sga_calcs/ndfd_sga_calcs.csv"))


# ---- 15. select area weighted ndfd cmu calcs for leases ----
# find leases that are in cmus
ndfd_lease_calcs_data_raw <- cmu_bounds_albers %>%
  st_intersection(lease_data_albers) %>%
  dplyr::select(lease_id, HA_CLASS) %>%
  st_drop_geometry() %>%
  # group_by(lease_id) %>%
  # count()
  dplyr::left_join(ndfd_cmu_calcs_data, by = "HA_CLASS") %>%
  dplyr::mutate(duplicate_id = paste0(lease_id, "_", rainfall_thresh_in)) # make a unique id for anti-join

# final tidy up of lease calcs for database
ndfd_lease_calcs_data_spread <- ndfd_lease_calcs_data_raw %>%
  dplyr::mutate(day = ymd(datetime_uct),
                prob_close = round(prob_close_perc, 0)) %>%
  dplyr::select(lease_id, day, valid_period_hrs, prob_close) %>%
  dplyr::mutate(valid_period = case_when(valid_period_hrs == 24 ~ "prob_1d_perc",
                                         valid_period_hrs == 48 ~ "prob_2d_perc",
                                         valid_period_hrs == 72 ~ "prob_3d_perc")) %>%
  dplyr::select(-valid_period_hrs) %>%
  tidyr::pivot_wider(id_cols = c(lease_id, day), 
                     names_from = valid_period, 
                     values_from = prob_close, 
                     values_fn = max) # will take the max prob. closure value if there are multiple
# some leases might overlap two cmus so account for that by taking cmu with minimum rainfall threshold
# for example lease_id = 64-75B includes NB_4 (2 in depth) and NB_5 (4 in depth/emergency)

# add in leases wihtout cmus as NA values
# these are leases that, at no point, touch a cmu boundary
# ndfd_leases_ignored_list <- lease_data_albers %>%
#   dplyr::anti_join(ndfd_lease_calcs_data_spread, by = "lease_id") %>%
#   st_drop_geometry() %>%
#   dplyr::select(lease_id)

# create dataframe to bind to ndfd_lease_calcs_data_spread
# ndfd_leases_ignored <- data.frame(lease_id = ndfd_leases_ignored_list$lease_id,
#                                   day = ndfd_date_uct,
#                                   prob_1d_perc = NA,
#                                   prob_2d_perc = NA,
#                                   prob_3d_perc = NA)

# final dataset
# ndfd_lease_calcs_data <- rbind(ndfd_lease_calcs_data_spread, ndfd_leases_ignored)
ndfd_lease_calcs_data <- ndfd_lease_calcs_data_spread

# check unique values
# length(ndfd_lease_calcs_data$lease_id) # 483 on 20200806
# length(unique(ndfd_lease_calcs_data$lease_id)) # 483 ok!


# ---- 16. export lease data ----
# write_csv(ndfd_lease_calcs_data, paste0(ndfd_tabular_data_output_path, "lease_calcs/ndfd_lease_calcs_", latest_ndfd_date_uct_str, ".csv")) # includes date in file name
write_csv(ndfd_lease_calcs_data, paste0(ndfd_tabular_data_output_path, "lease_calcs/ndfd_lease_calcs.csv"))


# ---- 17. save ignored leases ----

# save ignored leases
# ndfd_leases_ignored_data <- lease_data_albers %>%
#   dplyr::anti_join(ndfd_lease_calcs_data_spread, by = "lease_id")

# check crs
# st_crs(ndfd_leases_ignored_data)

# save ignored leases (as tabular)
# ndfd_leases_ignored_tab_data <- ndfd_leases_ignored_data %>%
#   st_drop_geometry()


# ---- 18. export data for ignored leases ----

# export ignored lease data
# st_write(ndfd_leases_ignored_data, paste0(lease_spatial_data_output_path, "lease_bounds_ignored_", latest_ndfd_date_uct_str, ".shp"))

# export ignored lease data (tabular)
# write_csv(ndfd_leases_ignored_tab_data, paste0(lease_tabular_data_output_path, "lease_bounds_ignored_", latest_ndfd_date_uct_str, ".csv"))


# ---- 19. append data for long-term analysis ----
# reformat cmu data
ndfd_cmu_calcs_data_to_append <- ndfd_cmu_calcs_data %>%
  dplyr::select(-row_num) %>%
  dplyr::mutate(flag = rep(notification_flag, dim(ndfd_cmu_calcs_data)[1]))

# reformat sga data
datetime_uct_now <- unique(ndfd_cmu_calcs_data_to_append$datetime_uct)
ndfd_sga_calcs_data_to_append <- ndfd_sga_calcs_data %>%
  ungroup() %>%
  dplyr::mutate(datetime_uct = rep(datetime_uct_now, dim(ndfd_sga_calcs_data)[1]),
                flag = rep(notification_flag, dim(ndfd_sga_calcs_data)[1])) %>%
  dplyr::select(grow_area_name, datetime_uct, min_1d_prob:max_3d_prob, flag)

# reformat lease data
ndfd_lease_calcs_data_to_append <- ndfd_lease_calcs_data %>%
  dplyr::mutate(flag = rep(notification_flag, dim(ndfd_lease_calcs_data)[1])) %>%
  dplyr::select(lease_id, datetime_uct = day, prob_1d_perc:flag)

# append all three datasets
write_csv(ndfd_cmu_calcs_data_to_append, path = paste0(ndfd_tabular_data_appended_output_path, "ndfd_cmu_calcs_appended.csv"), append = TRUE)
write_csv(ndfd_sga_calcs_data_to_append, path = paste0(ndfd_tabular_data_appended_output_path, "ndfd_sga_calcs_appended.csv"), append = TRUE)
write_csv(ndfd_lease_calcs_data_to_append, path = paste0(ndfd_tabular_data_appended_output_path, "ndfd_lease_calcs_appended.csv"), append = TRUE)



print("finished analyzing forecast data")
