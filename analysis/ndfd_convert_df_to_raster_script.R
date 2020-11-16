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

# TODO (wishlist) use here package


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
# path to ndfd tabular inputs
ndfd_tabular_data_input_path <- paste0(data_base_path, "tabular/outputs/ndfd_sco_data/ndfd_sco_data_raw/")

# path to nc buffer spatial inputs
nc_buffer_spatial_input_path <- paste0(data_base_path, "spatial/inputs/state_bounds_data/")

# path to ndfd spatial outputs
ndfd_spatial_data_output_path <- paste0(data_base_path, "spatial/outputs/ndfd_sco_data/")

# define proj4 string for ndfd data
ndfd_proj4 = "+proj=lcc +lat_1=25 +lat_2=25 +lat_0=25 +lon_0=-95 +x_0=0 +y_0=0 +a=6371000 +b=6371000 +units=m +no_defs"
# source: https://spatialreference.org/ref/sr-org/6825/

# define epsg and proj for CONUS Albers projection (projecting to this)
conus_albers_epsg <- 5070
conus_albers_proj <- "+init=EPSG:5070"

# define wgs 84 projection
# wgs84_epsg <- 4326
# wgs84_proj4 <- "+proj=longlat +datum=WGS84 +no_defs"


# ---- 4. pull latest ndfd file name (with dates) ----
# list files in ndfd_sco_data_raw
# ndfd_files <- list.files(ndfd_tabular_data_input_path, pattern = "pop12_*") # if there is a pop12 dataset there's a qpf dataset

# option 1: select based on minimum difference to current date, will always have result (but it might not be the most current)
# grab dates
# ndfd_file_dates <- lubridate::ymd(gsub("pop12_", "", gsub("00.csv", "", ndfd_files))) # assumes midnight

# save todya's date
# today_date_uct <- lubridate::today(tzone = "UCT")

# calcualte difference
# diff_ndfd_file_dates <- as.numeric(today_date_uct - ndfd_file_dates) # in days

# find position of smallest difference
# latest_ndfd_date_uct <- ndfd_file_dates[diff_ndfd_file_dates == min(diff_ndfd_file_dates)]

# convert to string
# latest_ndfd_date_uct_str <- strftime(latest_ndfd_date_uct, format = "%Y%m%d%H") # assumes midnight

# option 2: will give an empty latest_ndfd_date_uct variable, if exact day is not available
# grab dates
# ndfd_file_dates <- gsub("pop12_", "", gsub("00.csv", "", ndfd_files))

# save todya's date
# today_date_uct <- lubridate::today(tzone = "UCT")

# convert to string for later use
# today_date_uct_str <- strftime(today_date_uct, format = "%Y%m%d%H")

# check that date exists
# date_check <- ndfd_file_dates[ndfd_file_dates == today_date_uct_str]

# if statement that if length(date_check) < 1 then don't run this script
# latest_ndfd_date_uct_str <- today_date_uct_str


# ---- 5. load data ----
# latest ndfd path strings
# ndfd_latest_pop12_file_name <- paste0("pop12_", latest_ndfd_date_uct_str, ".csv") # includes date in file name
# ndfd_latest_qpf_file_name <- paste0("qpf_", latest_ndfd_date_uct_str, ".csv") # includes date in file name
ndfd_latest_pop12_file_name <- paste0("pop12.csv")
ndfd_latest_qpf_file_name <- paste0("qpf.csv")

# pop12 tabular data
ndfd_pop12_data_raw <- read_csv(paste0(ndfd_tabular_data_input_path, ndfd_latest_pop12_file_name),
                                col_types = list(col_double(), col_double(), col_double(), col_double(), col_double(), col_double(), col_double(),
                                                 col_character(), col_character(), col_character(), col_character(), col_character()))

# qpf tabular data
ndfd_qpf_data_raw <- read_csv(paste0(ndfd_tabular_data_input_path, ndfd_latest_qpf_file_name),
                              col_types = list(col_double(), col_double(), col_double(), col_double(), col_double(), col_double(), col_double(),
                                               col_character(), col_character(), col_character(), col_character(), col_character()))
# nc buffer bounds vector
nc_bounds_buffer_albers <- st_read(paste0(nc_buffer_spatial_input_path, "nc_bounds_10kmbuf_albers.shp"))
# st_crs(nc_bounds_buffer_albers) # crs = 5070, check!


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
  st_transform(crs = conus_albers_epsg)

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
  st_transform(crs = conus_albers_epsg)

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
                               crs = conus_albers_proj,
                               ext = extent(ndfd_pop12_albers_1day))
ndfd_pop12_grid_2day <- raster(ncol = length(unique(ndfd_pop12_albers_2day$longitude_km)),
                               nrows = length(unique(ndfd_pop12_albers_2day$latitude_km)),
                               crs = conus_albers_proj,
                               ext = extent(ndfd_pop12_albers_2day))
ndfd_pop12_grid_3day <- raster(ncol = length(unique(ndfd_pop12_albers_3day$longitude_km)),
                               nrows = length(unique(ndfd_pop12_albers_3day$latitude_km)),
                               crs = conus_albers_proj,
                               ext = extent(ndfd_pop12_albers_3day))

# make empty qpf raster for 1-day, 2-day, and 3-day forecasts
ndfd_qpf_grid_1day <- raster(ncol = length(unique(ndfd_qpf_albers_1day$longitude_km)),
                             nrows = length(unique(ndfd_qpf_albers_1day$latitude_km)),
                             crs = conus_albers_proj,
                             ext = extent(ndfd_qpf_albers_1day))
ndfd_qpf_grid_2day <- raster(ncol = length(unique(ndfd_qpf_albers_2day$longitude_km)),
                             nrows = length(unique(ndfd_qpf_albers_2day$latitude_km)),
                             crs = conus_albers_proj,
                             ext = extent(ndfd_qpf_albers_2day))
ndfd_qpf_grid_3day <- raster(ncol = length(unique(ndfd_qpf_albers_3day$longitude_km)),
                             nrows = length(unique(ndfd_qpf_albers_3day$latitude_km)),
                             crs = conus_albers_proj,
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

# plot to check
# plot(ndfd_pop12_raster_1day_albers)
# plot(ndfd_qpf_raster_1day_albers)
# plot(ndfd_pop12_raster_2day_albers)
# plot(ndfd_qpf_raster_2day_albers)
# plot(ndfd_pop12_raster_3day_albers)
# plot(ndfd_qpf_raster_3day_albers)


# ---- 9. crop midatlantic raster ndfd data to nc bounds ----
# pop12 for 1-day, 2-day, and 3-day forecasts
ndfd_pop12_raster_1day_nc_albers <- raster::crop(ndfd_pop12_raster_1day_albers, nc_bounds_buffer_albers)
ndfd_pop12_raster_2day_nc_albers <- raster::crop(ndfd_pop12_raster_2day_albers, nc_bounds_buffer_albers)
ndfd_pop12_raster_3day_nc_albers <- raster::crop(ndfd_pop12_raster_3day_albers, nc_bounds_buffer_albers)

# qpf for 1-day, 2-day, and 3-day forecasts
ndfd_qpf_raster_1day_nc_albers <- raster::crop(ndfd_qpf_raster_1day_albers, nc_bounds_buffer_albers)
ndfd_qpf_raster_2day_nc_albers <- raster::crop(ndfd_qpf_raster_2day_albers, nc_bounds_buffer_albers)
ndfd_qpf_raster_3day_nc_albers <- raster::crop(ndfd_qpf_raster_3day_albers, nc_bounds_buffer_albers)

# plot to check
# plot(nc_bounds_buffer_albers)
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

# ---- 10. export nc raster ndfd data (without date) ----
# export pop12 rasters for 1-day, 2-day, and 3-day forecasts
writeRaster(ndfd_pop12_raster_1day_nc_albers, paste0(ndfd_spatial_data_output_path, "pop12_24hr_nc_albers.tif"), overwrite = TRUE)
writeRaster(ndfd_pop12_raster_2day_nc_albers, paste0(ndfd_spatial_data_output_path, "pop12_48hr_nc_albers.tif"), overwrite = TRUE)
writeRaster(ndfd_pop12_raster_3day_nc_albers, paste0(ndfd_spatial_data_output_path, "pop12_72hr_nc_albers.tif"), overwrite = TRUE)

# export qpf rasters for 1-day, 2-day, and 3-day forecasts
writeRaster(ndfd_qpf_raster_1day_nc_albers, paste0(ndfd_spatial_data_output_path, "qpf_24hr_nc_albers.tif"), overwrite = TRUE)
writeRaster(ndfd_qpf_raster_2day_nc_albers, paste0(ndfd_spatial_data_output_path, "qpf_48hr_nc_albers.tif"), overwrite = TRUE)
writeRaster(ndfd_qpf_raster_3day_nc_albers, paste0(ndfd_spatial_data_output_path, "qpf_72hr_nc_albers.tif"), overwrite = TRUE)

# export pop12 rasters as wgs84 too for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_pop12_raster_1day_nc_wgs84, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct_str, "_24hr_nc_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_2day_nc_wgs84, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct_str, "_48hr_nc_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_3day_nc_wgs84, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct_str, "_72hr_nc_wgs84.tif"), overwrite = TRUE)

# export qpf rasters as wgs84 too for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_qpf_raster_1day_nc_wgs84, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct_str, "_24hr_nc_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_2day_nc_wgs84, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct_str, "_48hr_nc_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_3day_nc_wgs84, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct_str, "_72hr_nc_wgs84.tif"), overwrite = TRUE)


# ---- 11. export nc raster ndfd data (with date) ----
# export pop12 rasters for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_pop12_raster_1day_nc_albers, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct_str, "_24hr_nc_albers.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_2day_nc_albers, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct_str, "_48hr_nc_albers.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_3day_nc_albers, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct_str, "_72hr_nc_albers.tif"), overwrite = TRUE)

# export qpf rasters for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_qpf_raster_1day_nc_albers, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct_str, "_24hr_nc_albers.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_2day_nc_albers, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct_str, "_48hr_nc_albers.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_3day_nc_albers, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct_str, "_72hr_nc_albers.tif"), overwrite = TRUE)

# export pop12 rasters as wgs84 too for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_pop12_raster_1day_nc_wgs84, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct_str, "_24hr_nc_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_2day_nc_wgs84, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct_str, "_48hr_nc_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_3day_nc_wgs84, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct_str, "_72hr_nc_wgs84.tif"), overwrite = TRUE)

# export qpf rasters as wgs84 too for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_qpf_raster_1day_nc_wgs84, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct_str, "_24hr_nc_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_2day_nc_wgs84, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct_str, "_48hr_nc_wgs84.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_3day_nc_wgs84, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct_str, "_72hr_nc_wgs84.tif"), overwrite = TRUE)


print("finished converting df to raster")
