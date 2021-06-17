# ---- script header ----
# script name: ndfd_analyze_forecast_data_script.R
# purpose of script: takes raw ndfd tabular data and calculates probability of closure
# author: sheila saia
# date created: 20200525
# email: ssaia@ncsu.edu
# ---- revision ----
# purpose of revision: takes raw ndfd tabular data and outputs summarized data that are used in machine learning models to predict area-weighted precipitation for each cmu
# revised by: natalie nelson
# date revision created: 20210608
# email: nnelson4@ncsu.edu


# ---- notes ----
# notes:


# ---- to do ----
# to do list

# TODO include error message/script stopping for no recent data to pull
# TODO (wishlist) use terra package for raster stuff
# TODO remove notification testing factor when testing is over



# ---- 1. install and load packages as necessary ----
# packages
packages <- c("tidyverse", "raster", "sf", "lubridate", "here")

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
# data_base_path = "/Users/sheila/Documents/github_ncsu/shellcast/analysis/data/"
data_base_path = here::here("data")


# ---- 3. use base paths and define projections ----
# inputs
# path to ndfd spatial inputs
ndfd_spatial_data_input_path <- paste0(data_base_path, "/spatial/outputs/ndfd_sco_data/")

# path to sga buffer spatial inputs
sga_spatial_data_input_path <- paste0(data_base_path, "/spatial/inputs/ncdmf_data/sga_bounds/")

# path to cmu bounds spatial inputs
cmu_spatial_data_input_path <- paste0(data_base_path, "/spatial/inputs/ncdmf_data/cmu_bounds/")

# path to lease bounds spatial inputs
lease_spatial_data_input_path <- paste0(data_base_path, "/spatial/outputs/ncdmf_data/lease_centroids/")

# path to rainfall threshold tabular inputs
rainfall_thresh_tabular_data_input_path <- paste0(data_base_path, "/tabular/inputs/ncdmf_rainfall_thresholds/")

# outputs
# path to ndfd spatial outputs
ndfd_spatial_data_output_path <- paste0(data_base_path, "/spatial/outputs/ndfd_sco_data/")

# path to ndfd tabular outputs
ndfd_tabular_data_output_path <- paste0(data_base_path, "/tabular/outputs/ndfd_sco_data/")

# path to ndfd tabular outputs appended
ndfd_tabular_data_appended_output_path <- paste0(data_base_path, "/tabular/outputs/ndfd_sco_data_appended/")

# projections
# define proj4 string for ndfd data
ndfd_proj4 = "+proj=lcc +lat_1=25 +lat_2=25 +lat_0=25 +lon_0=-95 +x_0=0 +y_0=0 +a=6371000 +b=6371000 +units=m +no_defs"
# source: https://spatialreference.org/ref/sr-org/6825/

# define epsg and proj for CONUS Albers projection (projecting to this)
conus_albers_epsg <- 5070
conus_albers_proj <- "+init=EPSG:5070"

# notification flag for testing or production versions
notification_flag <- "production" # "testing" or "production"
notification_dist_min <- 0 # for notification_flag <- "testing"
notification_dist_max <- 100 # for notification_flag <- "testing"
# notification_factor <- 3


# ---- 4. load other data ----
# raster data
# latest pop12 ndfd data raster for 1-day, 2-day, and 3-day forecasts
ndfd_pop12_raster_1day_nc_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "pop12_24hr_nc_albers.tif"))
ndfd_pop12_raster_2day_nc_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "pop12_48hr_nc_albers.tif"))
ndfd_pop12_raster_3day_nc_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "pop12_72hr_nc_albers.tif"))

# check projection
# crs(ndfd_pop12_raster_1day_nc_albers)
# crs(ndfd_pop12_raster_2day_nc_albers)
# crs(ndfd_pop12_raster_3day_nc_albers)

# latest qpf ndfd data raster for 1-day, 2-day, and 3-day forecasts
ndfd_qpf_raster_1day_nc_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "qpf_24hr_nc_albers.tif")) # includes date in file name
ndfd_qpf_raster_2day_nc_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "qpf_48hr_nc_albers.tif")) # includes date in file name
ndfd_qpf_raster_3day_nc_albers <- raster::raster(paste0(ndfd_spatial_data_input_path, "qpf_72hr_nc_albers.tif")) # includes date in file name

# check projection
# crs(ndfd_qpf_raster_1day_nc_albers)
# crs(ndfd_qpf_raster_2day_nc_albers)
# crs(ndfd_qpf_raster_3day_nc_albers)

# spatial data
# sga bounds buffered
sga_bounds_buffer_albers <- st_read(paste0(sga_spatial_data_input_path, "sga_bounds_10kmbuf_albers.shp"))

# sga data
sga_bounds_simple_albers <- st_read(paste0(sga_spatial_data_input_path, "sga_bounds_simple_albers.shp"))

# cmu bounds buffered
cmu_bounds_buffer_albers <- st_read(paste0(cmu_spatial_data_input_path, "cmu_bounds_10kmbuf_albers.shp"))

# cmu bounds
cmu_bounds_albers <- st_read(paste0(cmu_spatial_data_input_path, "cmu_bounds_albers.shp"))

# lease centroids
lease_centroids_albers <- st_read(paste0(lease_spatial_data_input_path, "lease_centroids_albers.shp"))

# all spatial data should have crs = 5070
# check crs
# st_crs(sga_bounds_buffer_albers)
# st_crs(sga_bounds_simple_albers)
# st_crs(cmu_bounds_buffer_albers)
# st_crs(cmu_bounds_albers)
# st_crs(lease_data_albers)

# tabular data
# rainfall thresholds
rainfall_thresholds_raw_tidy <- read_csv(paste0(rainfall_thresh_tabular_data_input_path, "rainfall_thresholds_raw_tidy.csv"))

# cmu sga key
cmu_sga_key <- read_csv(paste0(rainfall_thresh_tabular_data_input_path, "cmu_sga_key.csv"))

# ---- 5. crop sga or nc raster ndfd data to cmu bounds ----
# 1-day pop12 for 1-day, 2-day, and 3-day forecasts
ndfd_pop12_raster_1day_cmu_albers <- raster::mask(ndfd_pop12_raster_1day_nc_albers, mask = cmu_bounds_buffer_albers)
ndfd_pop12_raster_2day_cmu_albers <- raster::mask(ndfd_pop12_raster_2day_nc_albers, mask = cmu_bounds_buffer_albers)
ndfd_pop12_raster_3day_cmu_albers <- raster::mask(ndfd_pop12_raster_3day_nc_albers, mask = cmu_bounds_buffer_albers)

# plot to check
# plot(ndfd_pop12_raster_1day_cmu_albers)
# plot(ndfd_pop12_raster_2day_cmu_albers)
# plot(ndfd_pop12_raster_3day_cmu_albers)

# 1-day qpf for 1-day, 2-day, and 3-day forecasts
ndfd_qpf_raster_1day_cmu_albers <-  raster::mask(ndfd_qpf_raster_1day_nc_albers, mask = cmu_bounds_buffer_albers)
ndfd_qpf_raster_2day_cmu_albers <-  raster::mask(ndfd_qpf_raster_2day_nc_albers, mask = cmu_bounds_buffer_albers)
ndfd_qpf_raster_3day_cmu_albers <-  raster::mask(ndfd_qpf_raster_3day_nc_albers, mask = cmu_bounds_buffer_albers)

# plot to check
# plot(ndfd_qpf_raster_1day_cmu_albers)
# plot(ndfd_qpf_raster_2day_cmu_albers)
# plot(ndfd_qpf_raster_3day_cmu_albers)


# ---- 6. export cmu raster ndfd data ----
# export pop12 rasters for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_pop12_raster_1day_cmu_albers, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct, "_24hr_cmu_albers.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_2day_cmu_albers, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct, "_48hr_cmu_albers.tif"), overwrite = TRUE)
# writeRaster(ndfd_pop12_raster_3day_cmu_albers, paste0(ndfd_spatial_data_output_path, "pop12_", latest_ndfd_date_uct, "_78hr_cmu_albers.tif"), overwrite = TRUE)

# export qpf rasters for 1-day, 2-day, and 3-day forecasts
# writeRaster(ndfd_qpf_raster_1day_cmu_albers, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct, "_24hr_cmu_albers.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_2day_cmu_albers, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct, "_48hr_cmu_albers.tif"), overwrite = TRUE)
# writeRaster(ndfd_qpf_raster_3day_cmu_albers, paste0(ndfd_spatial_data_output_path, "qpf_", latest_ndfd_date_uct, "_72hr_cmu_albers.tif"), overwrite = TRUE)


# ---- 7. area weighted ndfd cmu calcs ----
# need to do this for pop12 and qpf and for 1-day, 2-day, and 3-day forecasts
ndfd_cmu_calcs_data <- data.frame(row_num = as.numeric(),
                                  cmu_name = as.character(),
                                  rainfall_thresh_in = as.numeric(),
                                  datetime_uct = as.character(),
                                  month = as.numeric(),
                                  valid_period_hrs = as.numeric(),
                                  pop12_perc = as.numeric(),
                                  qpf_in = as.numeric())
                                  # prob_close_perc = as.numeric() # REMOVE FOR NEW ML WORKFLOW

# valid period list
valid_period_list <- c(24, 48, 72)

# define date
ndfd_date_uct <- lubridate::today(tzone = "UCT")

# rasters lists
pop12_cmu_raster_list <- c(ndfd_pop12_raster_1day_cmu_albers, 
                           ndfd_pop12_raster_2day_cmu_albers, 
                           ndfd_pop12_raster_3day_cmu_albers)
qpf_cmu_raster_list <- c(ndfd_qpf_raster_1day_cmu_albers, 
                         ndfd_qpf_raster_2day_cmu_albers, 
                         ndfd_qpf_raster_3day_cmu_albers)

# number of cmu's
num_cmu <- length(cmu_bounds_albers$cmu_name)

# row dimentions
num_cmu_row <- length(valid_period_list) * num_cmu

# set row number and start iterator
cmu_row_num_list <- seq(1:num_cmu_row)
cmu_row_num <- cmu_row_num_list[1]

# record start time
start_time <- now()

# for loop
# i denotes valid period (3 values), j denotes cmu_name
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
    temp_cmu_name <- as.character(cmu_bounds_albers$cmu_name[j])

    # save cmu rainfall threshold value
    temp_cmu_rain_in <- as.numeric(cmu_bounds_albers$rain_in[j])

    # get cmu bounds vector
    temp_cmu_bounds <- cmu_bounds_albers %>%
      dplyr::filter(cmu_name == temp_cmu_name)

    # cmu bounds area
    temp_cmu_area <- as.numeric(st_area(temp_cmu_bounds)) # in m^2
    
    # get value and weight of each gridcell that overlaps the cmu
    temp_pop12_cmu_raster_perc_cover_df <- data.frame(raster::extract(temp_pop12_raster, temp_cmu_bounds, weights = TRUE)[[1]]) # getCover give percentage of the cover of the cmu boundary in the raster
    temp_qpf_cmu_raster_perc_cover_df <- data.frame(raster::extract(temp_qpf_raster, temp_cmu_bounds, weights = TRUE)[[1]]) # getCover give percentage of the cover of the cmu boundary in the raster
    
    # calculate area weighted avg value for the cmu
    temp_pop12_area_weighted_df <- temp_pop12_cmu_raster_perc_cover_df %>%
      dplyr::mutate(area_weighted_avg = value * weight)
    temp_qpf_area_weighted_df <- temp_qpf_cmu_raster_perc_cover_df %>%
      dplyr::mutate(area_weighted_avg = value * weight)
    
    # sum weighted values to get result
    temp_cmu_pop12_result <- round(sum(temp_pop12_area_weighted_df$area_weighted_avg), 2)
    temp_cmu_qpf_result <- round(sum(temp_qpf_area_weighted_df$area_weighted_avg), 2)
    
    # --- REMOVE FOR NEW ML WORKFLOW ---
    # calculate probability of closure
    # check if testing mode
    # if not testing mode calculate probability of closure as you would in production
    # if (notification_flag == "production") {
      #temp_cmu_prob_close_result <- round((temp_cmu_pop12_result * exp(-temp_cmu_rain_in / temp_cmu_qpf_result)), 1) # from equation 1 in proposal
    # }

    # if testing mode then more frequent approach to ensure more frequent notifications
    # else {
      # num_vals <- length(temp_cmu_qpf_result)
      # random_unif_vals <- round(runif(num_vals, min = notification_dist_min, max = notification_dist_max), 1) # random uniform distribution
      # temp_cmu_prob_close_result <- random_unif_vals
      # temp_cmu_prob_closure_result <- if_else(temp_cmu_prob_close_result * notification_factor > 100, 100, temp_cmu_prob_close_result * notification_factor) # to test notifications
    # }

    # save data
    temp_ndfd_cmu_calcs_data <- data.frame(row_num = cmu_row_num,
                                           cmu_name = temp_cmu_name,
                                           rainfall_thresh_in = temp_cmu_rain_in,
                                           datetime_uct = ndfd_date_uct,
                                           month = lubridate::month(ndfd_date_uct),
                                           valid_period_hrs = temp_valid_period,
                                           pop12_perc = temp_cmu_pop12_result,
                                           qpf_in = temp_cmu_qpf_result)
                                           # prob_close_perc = temp_cmu_prob_close_result) # REMOVE FOR NEW ML WORKFLOW

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


# ---- 8. reformat cmu calcs for db ----
# --- REMOVE FOR NEW ML WORKFLOW; USE IN LATER SCRIPT ---
# cmu_name, prob_1d_perc, prob_2d_perc, prob_3d_perc
# ndfd_cmu_calcs_data_spread <- ndfd_cmu_calcs_data %>%
#   dplyr::mutate(day = ymd(datetime_uct),
#                 prob_close = round(prob_close_perc, 0)) %>%
#   dplyr::select(cmu_name, day, valid_period_hrs, prob_close) %>%
#   dplyr::mutate(valid_period = case_when(valid_period_hrs == 24 ~ "prob_1d_perc",
#                                          valid_period_hrs == 48 ~ "prob_2d_perc",
#                                          valid_period_hrs == 72 ~ "prob_3d_perc")) %>%
#   dplyr::select(-valid_period_hrs) %>%
#   tidyr::pivot_wider(id_cols = c(cmu_name, day),
#                      names_from = valid_period,
#                      values_from = prob_close,
#                      values_fn = max) %>% # will take the max prob. closure value if there are multiple
#   dplyr::select(-day)

# View(ndfd_cmu_calcs_data_spread)


# ---- 9. export area weighted, spreaded ndfd cmu calcs ----
# export area weighted averages for qpf, pop for each cmu
# write_csv(ndfd_cmu_calcs_data_spread, paste0(ndfd_tabular_data_output_path, "cmu_calcs/ndfd_cmu_calcs.csv"))
write_csv(ndfd_cmu_calcs_data, paste0(ndfd_tabular_data_output_path, "cmu_calcs/ndfd_cmu_calcs.csv"))
# export data in 24h, 48h, and 72h subsets
ndfd_cmu_calcs_data_24 <- ndfd_cmu_calcs_data %>% filter(valid_period_hrs == 24)
ndfd_cmu_calcs_data_48 <- ndfd_cmu_calcs_data %>% filter(valid_period_hrs == 48)
ndfd_cmu_calcs_data_72 <- ndfd_cmu_calcs_data %>% filter(valid_period_hrs == 72)
write_csv(ndfd_cmu_calcs_data_24, paste0(ndfd_tabular_data_output_path, "cmu_calcs/ndfd_cmu_calcs_24h.csv"))
write_csv(ndfd_cmu_calcs_data_48, paste0(ndfd_tabular_data_output_path, "cmu_calcs/ndfd_cmu_calcs_48h.csv"))
write_csv(ndfd_cmu_calcs_data_72, paste0(ndfd_tabular_data_output_path, "cmu_calcs/ndfd_cmu_calcs_72h.csv"))

print("finished analyzing forecast data")


# ---- 10. append data for long-term analysis ----
# --- REMOVE FOR NEW ML WORKFLOW; USE IN LATER SCRIPT ---
# # reformat cmu data
# ndfd_cmu_calcs_data_to_append <- ndfd_cmu_calcs_data %>%
#   dplyr::select(-row_num) %>%
#   dplyr::mutate(flag = rep(notification_flag, dim(ndfd_cmu_calcs_data)[1]))
# 
# # append all three datasets
# write_csv(ndfd_cmu_calcs_data_to_append, path = paste0(ndfd_tabular_data_appended_output_path, "ndfd_cmu_calcs_appended.csv"), append = TRUE)
# 
# print("appended forecast data for long-term analysis")