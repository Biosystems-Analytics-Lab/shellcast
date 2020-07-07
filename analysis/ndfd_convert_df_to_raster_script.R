# ---- script header ----
# script name: ndfd_convert_df_to_raster_script.R
# purpose of script: converts latest raw ndfd dataframes to raster data for downstream forecast analysis
# author: sheila saia
# date created: 20200622
# email: ssaia@ncsu.edu


# ---- notes ----
# notes:


# ---- to do ----
# to do list

# TODO finish date_check if statement
# TODO fix latest load in


# ---- 1. install packages ----
# only need to install these once
# install.packages("tidyverse")
# install.packages("raster")
# install.packages("sf")
# install.packages("lubridate")


# ---- 2. load packages ----
library(tidyverse)
library(raster)
library(sf)
library(lubridate)


# ---- 3. defining paths and projections ----
# path to data
ndfd_data_path <- ".../analysis/data/tabular/ndfd_sco_data_raw/"

# nc buffer data path
nc_bounds_buffer_path <- ".../analysis/data/spatial/generated/region_state_bounds/"

# exporting ndfd raster spatial data path
ndfd_sco_spatial_data_export_path <- ".../analysis/data/spatial/generated/ndfd_sco_data/"

# define proj4 string for ndfd data
ndfd_proj4 = "+proj=lcc +lat_1=25 +lat_2=25 +lat_0=25 +lon_0=-95 +x_0=0 +y_0=0 +a=6371000 +b=6371000 +units=m +no_defs"
# source: https://spatialreference.org/ref/sr-org/6825/

# define epsg and proj4 for N. America Albers projection (projecting to this)
na_albers_proj4 <- "+proj=aea +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs"
na_albers_epsg <- 102008

# define wgs 84 projection
wgs84_epsg <- 4326
wgs84_proj4 <- "+proj=longlat +datum=WGS84 +no_defs"


# ---- 4. pull latest ndfd file name ----
# list files in ndfd_sco_data_raw
ndfd_files <- list.files(ndfd_data_path, pattern = "pop12_*") # if there is a pop12 dataset there's a qpf dataset

# grab dates
ndfd_file_dates <- gsub("pop12_", "", gsub(".csv", "", ndfd_files))

# save todya's date
today_date_uct <- lubridate::today(tzone = "UCT")

# convert to string for later use
today_date_uct_str <- strftime(today_date_uct, format = "%Y%m%d%H")

# check that date exists
date_check <- ndfd_file_dates[ndfd_file_dates == today_date_uct_str]

# if statement that if length(date_check) < 1 then don't run this script
latest_uct_str <- today_date_uct_str


# ---- 5. load data ----
# latest ndfd path strings
ndfd_latest_pop12_file_name <- paste0("pop12_", latest_uct_str, ".csv")
ndfd_latest_qpf_file_name <- paste0("qpf_", latest_uct_str, ".csv")

# pop12 tabular data
ndfd_pop12_data_raw <- read_csv(paste0(ndfd_data_path, ndfd_latest_pop12_file_name),
                                col_types = list(col_double(), col_double(), col_double(), col_double(), col_double(), col_double(), col_double(),
                                                 col_character(), col_character(), col_character(), col_character(), col_character()))

# qpf tabular data
ndfd_qpf_data_raw <- read_csv(paste0(ndfd_data_path, ndfd_latest_qpf_file_name),
                              col_types = list(col_double(), col_double(), col_double(), col_double(), col_double(), col_double(), col_double(),
                                               col_character(), col_character(), col_character(), col_character(), col_character()))
# nc buffer bounds vector
nc_buffer_albers <- st_read(paste0(nc_bounds_buffer_path, "nc_bounds_10kmbuf_albers.shp"))


# ---- 6. wrangle ndfd tabular data ----
# initial clean up pop12
ndfd_pop12_data <- ndfd_pop12_data_raw %>%
  dplyr::select(x_index, y_index, latitude_km, longitude_km, time_uct, time_nyc, pop12_value_perc, valid_period_hrs) %>%
  dplyr::mutate(latitude_m = latitude_km * 1000,
                longitude_m = longitude_km * 1000)

# initial clean up qpf
ndfd_qpf_data <- ndfd_qpf_data_raw %>%
  dplyr::select(x_index, y_index, latitude_km, longitude_km, time_uct, time_nyc, qpf_value_kgperm2, valid_period_hrs) %>%
  dplyr::mutate(latitude_m = latitude_km * 1000,
                longitude_m = longitude_km * 1000,
                qpf_value_in = qpf_value_kgperm2 * (1/1000) * (100) * (1/2.54)) # convert to m (density of water is 1000 kg/m3) then cm then inches


# ---- 7. convert tabular ndfd data to (vector) spatial data ----
# pop12
# convert pop12 to spatial data
ndfd_pop12_albers <- st_as_sf(ndfd_pop12_data,
                              coords = c("longitude_m", "latitude_m"),
                              crs = ndfd_proj4,
                              dim = "XY") %>%
  st_transform(crs = na_albers_epsg)

# check pop12 projection
# st_crs(ndfd_pop12_albers)
# look good!

# pop12 periods available
# unique(ndfd_pop12_albers$valid_period_hrs)

# select 1-day pop12
ndfd_pop12_albers_1day <- ndfd_pop12_albers %>%
  dplyr::filter(valid_period_hrs == 24)

# select 2-day pop12
ndfd_pop12_albers_2day <- ndfd_pop12_albers %>%
  dplyr::filter(valid_period_hrs == 48)

# select 3-day pop12
ndfd_pop12_albers_3day <- ndfd_pop12_albers %>%
  dplyr::filter(valid_period_hrs == 72)

# qpf
# convert qpf to spatial data
ndfd_qpf_albers <- st_as_sf(ndfd_qpf_data,
                            coords = c("longitude_m", "latitude_m"),
                            crs = ndfd_proj4,
                            dim = "XY") %>%
  st_transform(crs = na_albers_epsg)

# check qpf projection
# st_crs(ndfd_qpf_albers)
# look good!

# qpf periods available
# unique(ndfd_qpf_albers$valid_period_hrs)

# select 1-day qpf
ndfd_qpf_albers_1day <- ndfd_qpf_albers %>%
  dplyr::filter(valid_period_hrs == 24)

# select 2-day qpf
ndfd_qpf_albers_2day <- ndfd_qpf_albers %>%
  dplyr::filter(valid_period_hrs == 48)

# select 3-day qpf
ndfd_qpf_albers_3day <- ndfd_qpf_albers %>%
  dplyr::filter(valid_period_hrs == 72)


# ---- 8. convert vector ndfd data to raster data ----
# make empty pop12 raster for 1-day, 2-day, and 3-day forecasts
ndfd_pop12_grid_1day <- raster(ncol = length(unique(ndfd_pop12_albers_1day$longitude_km)),
                               nrows = length(unique(ndfd_pop12_albers_1day$latitude_km)),
                               crs = na_albers_proj4,
                               ext = extent(ndfd_pop12_albers_1day))
ndfd_pop12_grid_2day <- raster(ncol = length(unique(ndfd_pop12_albers_2day$longitude_km)),
                               nrows = length(unique(ndfd_pop12_albers_2day$latitude_km)),
                               crs = na_albers_proj4,
                               ext = extent(ndfd_pop12_albers_2day))
ndfd_pop12_grid_3day <- raster(ncol = length(unique(ndfd_pop12_albers_3day$longitude_km)),
                               nrows = length(unique(ndfd_pop12_albers_3day$latitude_km)),
                               crs = na_albers_proj4,
                               ext = extent(ndfd_pop12_albers_3day))

# make empty qpf raster for 1-day, 2-day, and 3-day forecasts
ndfd_qpf_grid_1day <- raster(ncol = length(unique(ndfd_qpf_albers_1day$longitude_km)),
                             nrows = length(unique(ndfd_qpf_albers_1day$latitude_km)),
                             crs = na_albers_proj4,
                             ext = extent(ndfd_qpf_albers_1day))
ndfd_qpf_grid_2day <- raster(ncol = length(unique(ndfd_qpf_albers_2day$longitude_km)),
                             nrows = length(unique(ndfd_qpf_albers_2day$latitude_km)),
                             crs = na_albers_proj4,
                             ext = extent(ndfd_qpf_albers_2day))
ndfd_qpf_grid_3day <- raster(ncol = length(unique(ndfd_qpf_albers_3day$longitude_km)),
                             nrows = length(unique(ndfd_qpf_albers_3day$latitude_km)),
                             crs = na_albers_proj4,
                             ext = extent(ndfd_qpf_albers_3day))

# rasterize pop12 for 1-day, 2-day, and 3-day forecasts
ndfd_pop12_raster_1day_albers <- raster::rasterize(ndfd_pop12_albers_1day, ndfd_pop12_grid_1day, field = ndfd_pop12_albers_1day$pop12_value_perc, fun = mean)
ndfd_pop12_raster_2day_albers <- raster::rasterize(ndfd_pop12_albers_2day, ndfd_pop12_grid_2day, field = ndfd_pop12_albers_2day$pop12_value_perc, fun = mean)
ndfd_pop12_raster_3day_albers <- raster::rasterize(ndfd_pop12_albers_3day, ndfd_pop12_grid_3day, field = ndfd_pop12_albers_3day$pop12_value_perc, fun = mean)
# crs(ndfd_pop12_grid_1day_albers)

# rasterize qpf for 1-day, 2-day, and 3-day forecasts
ndfd_qpf_raster_1day_albers <- raster::rasterize(ndfd_qpf_albers_1day, ndfd_qpf_grid_1day, field = ndfd_qpf_albers_1day$qpf_value_in, fun = mean)
ndfd_qpf_raster_2day_albers <- raster::rasterize(ndfd_qpf_albers_2day, ndfd_qpf_grid_2day, field = ndfd_qpf_albers_2day$qpf_value_in, fun = mean)
ndfd_qpf_raster_3day_albers <- raster::rasterize(ndfd_qpf_albers_3day, ndfd_qpf_grid_3day, field = ndfd_qpf_albers_3day$qpf_value_in, fun = mean)
# crs(ndfd_qpf_grid_1day_albers)
# na_albers_proj4 # it's missing the ellps-GRS80, not sure why...

# plot to check
# plot(ndfd_pop12_raster_1day_albers)
# plot(ndfd_qpf_raster_1day_albers)
# plot(ndfd_pop12_raster_2day_albers)
# plot(ndfd_qpf_raster_2day_albers)
# plot(ndfd_pop12_raster_3day_albers)
# plot(ndfd_qpf_raster_3day_albers)


# ---- 9. crop midatlantic raster ndfd data to nc bounds ----
# pop12 for 1-day, 2-day, and 3-day forecasts
ndfd_pop12_raster_1day_nc_albers <- raster::crop(ndfd_pop12_raster_1day_albers, nc_buffer_albers)
ndfd_pop12_raster_2day_nc_albers <- raster::crop(ndfd_pop12_raster_2day_albers, nc_buffer_albers)
ndfd_pop12_raster_3day_nc_albers <- raster::crop(ndfd_pop12_raster_3day_albers, nc_buffer_albers)

# qpf for 1-day, 2-day, and 3-day forecasts
ndfd_qpf_raster_1day_nc_albers <- raster::crop(ndfd_qpf_raster_1day_albers, nc_buffer_albers)
ndfd_qpf_raster_2day_nc_albers <- raster::crop(ndfd_qpf_raster_2day_albers, nc_buffer_albers)
ndfd_qpf_raster_3day_nc_albers <- raster::crop(ndfd_qpf_raster_3day_albers, nc_buffer_albers)

# plot to check
# plot(nc_buffer_albers)
# plot(ndfd_pop12_raster_1day_nc_albers)
# plot(ndfd_qpf_raster_1day_nc_albers)
# plot(ndfd_pop12_raster_2day_nc_albers)
# plot(ndfd_qpf_raster_2day_nc_albers)
# plot(ndfd_pop12_raster_3day_nc_albers)
# plot(ndfd_qpf_raster_3day_nc_albers)

# project pop12 to wgs84 toofor 1-day, 2-day, and 3-day forecasts
# ndfd_pop12_raster_1day_nc_wgs84 <- projectRaster(ndfd_pop12_raster_1day_nc_albers, crs = wgs84_proj4)
# ndfd_pop12_raster_2day_nc_wgs84 <- projectRaster(ndfd_pop12_raster_2day_nc_albers, crs = wgs84_proj4)
# ndfd_pop12_raster_3day_nc_wgs84 <- projectRaster(ndfd_pop12_raster_3day_nc_albers, crs = wgs84_proj4)

# project qpf to wgs84 too for 1-day, 2-day, and 3-day forecasts
# ndfd_qpf_raster_1day_nc_wgs84 <- projectRaster(ndfd_qpf_raster_1day_nc_albers, crs = wgs84_proj4)
# ndfd_qpf_raster_2day_nc_wgs84 <- projectRaster(ndfd_qpf_raster_2day_nc_albers, crs = wgs84_proj4)
# ndfd_qpf_raster_3day_nc_wgs84 <- projectRaster(ndfd_qpf_raster_3day_nc_albers, crs = wgs84_proj4)

# plot to check
# plot(ndfd_pop12_raster_1day_nc_wgs84)
# plot(ndfd_qpf_raster_1day_nc_wgs84)
# plot(ndfd_pop12_raster_2day_nc_wgs84)
# plot(ndfd_qpf_raster_2day_nc_wgs84)
# plot(ndfd_pop12_raster_3day_nc_wgs84)
# plot(ndfd_qpf_raster_3day_nc_wgs84)


# ---- 10. export nc raster ndfd data ----
# export pop12 rasters for 1-day, 2-day, and 3-day forecasts
writeRaster(ndfd_pop12_raster_1day_nc_albers, paste0(ndfd_sco_spatial_data_export_path, "pop12_", latest_uct_str, "_24hr_nc_albers.tif"), overwrite = TRUE)
writeRaster(ndfd_pop12_raster_2day_nc_albers, paste0(ndfd_sco_spatial_data_export_path, "pop12_", latest_uct_str, "_48hr_nc_albers.tif"), overwrite = TRUE)
writeRaster(ndfd_pop12_raster_3day_nc_albers, paste0(ndfd_sco_spatial_data_export_path, "pop12_", latest_uct_str, "_72hr_nc_albers.tif"), overwrite = TRUE)

# export qpf rasters for 1-day, 2-day, and 3-day forecasts
writeRaster(ndfd_qpf_raster_1day_nc_albers, paste0(ndfd_sco_spatial_data_export_path, "qpf_", latest_uct_str, "_24hr_nc_albers.tif"), overwrite = TRUE)
writeRaster(ndfd_qpf_raster_2day_nc_albers, paste0(ndfd_sco_spatial_data_export_path, "qpf_", latest_uct_str, "_48hr_nc_albers.tif"), overwrite = TRUE)
writeRaster(ndfd_qpf_raster_3day_nc_albers, paste0(ndfd_sco_spatial_data_export_path, "qpf_", latest_uct_str, "_72hr_nc_albers.tif"), overwrite = TRUE)

# export pop12 rasters as wgs84 too for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_pop12_raster_1day_nc_wgs84, paste0(ndfd_sco_spatial_data_export_path, "pop12_", latest_uct_str, "_24hr_nc_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_2day_nc_wgs84, paste0(ndfd_sco_spatial_data_export_path, "pop12_", latest_uct_str, "_48hr_nc_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_3day_nc_wgs84, paste0(ndfd_sco_spatial_data_export_path, "pop12_", latest_uct_str, "_72hr_nc_wgs84.tif"), overwrite = TRUE)

# export qpf rasters as wgs84 too for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_qpf_raster_1day_nc_wgs84, paste0(ndfd_sco_spatial_data_export_path, "qpf_", latest_uct_str, "_24hr_nc_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_2day_nc_wgs84, paste0(ndfd_sco_spatial_data_export_path, "qpf_", latest_uct_str, "_48hr_nc_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_3day_nc_wgs84, paste0(ndfd_sco_spatial_data_export_path, "qpf_", latest_uct_str, "_72hr_nc_wgs84.tif"), overwrite = TRUE)
