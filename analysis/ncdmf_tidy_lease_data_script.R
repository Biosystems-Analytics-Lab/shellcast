# ---- script header ----
# script name: ncdmf_tidy_lease_data_script.R
# purpose of script: tidy up lease data from nc dmf rest api (assumes data is in .shp format)
# author: sheila saia
# date created: 20200617
# email: ssaia@ncsu.edu


# ---- notes ----
# notes:

# raw data column metadata
# ProductNbr - lease id
# Assoc_ID - another id associated with the lease id (we don't need to worry about this)
# Owner - owner/business name
# Bus_Agent - business agent
# County - NC county that the business is in
# WB_Name - waterbody name (this is not the same as growing area)
# Type_ - lease type (bottom - rent rights to bottom, water column, franchise - own rights to bottom, research sanctuary, proposed, terminated)
# Status - status of the lease (there are lots of different unique values here)
# A_Granted - acres granted in the lease
# EffectiveD - date approved/renewed
# Expiration - expiration date of lease, 9996 and 9994 indicate a franchise - these have no expiration dates and if part or all is not in a cmu then can't harvest from it
# Term_Date - termination date (i.e., date when the leased area was terminated)


# ---- to do ----
# to do list

# TODO need to export file with lease_id and geo bounds for database
# TODO save all spatial data outputs to geojson (to reduce storage demands)
# TODO (wishlist) use here package


# ---- 1. install and load packages as necessary ----
# packages
packages <- c("tidyverse", "sf", "geojsonsf")

# install and load
for (package in packages) {
  if (! package %in% installed.packages()) {
    install.packages(package, dependencies = TRUE)
  }
  library(package, character.only = TRUE)
}


# ---- 2. define base paths ----
# base path to data
data_base_path = "opt/shellcast/analysis/data/" # set this and uncomment!
# data_base_path = "/Users/sheila/Documents/bae_shellcast_project/shellcast_analysis/web_app_data/" 


# ---- 3. defining paths and projections ----
# path to raw lease spatial inputs
lease_data_spatial_input_path <- paste0(data_base_path, "spatial/outputs/ncdmf_data/lease_bounds_raw/")

# path to cmu buffer spatial inputs
cmu_spatial_data_input_path <- paste0(data_base_path, "spatial/inputs/ncdmf_data/cmu_bounds/")

# path to rainfall threshold tabular inputs
rainfall_thresh_tabular_data_input_path <- paste0(data_base_path, "tabular/inputs/ncdmf_rainfall_thresholds/")


# path to lease spatial outputs
lease_data_spatial_output_path <-  paste0(data_base_path, "spatial/outputs/ncdmf_data/")


# define epsg and proj4 for N. America Albers projection (projecting to this)
na_albers_proj4 <- "+proj=aea +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs"
na_albers_epsg <- 102008

# define wgs 84 projection
wgs84_epsg <- 4326
wgs84_proj4 <- "+proj=longlat +datum=WGS84 +no_defs"


# ---- 4a. load in lease and rainfall threshold data (without dates) ----
# spatial data
# use latest date to read in most recent data
lease_bounds_raw <- st_read(paste0(lease_data_spatial_input_path, "lease_bounds_raw.shp"))

# check projection
# st_crs(lease_bounds_raw) # epsg = 2264

# cmu data
cmu_bounds_albers <- st_read(paste0(cmu_spatial_data_input_path, "cmu_bounds_albers.shp"))  %>%
  st_set_crs(na_albers_epsg) # epsg code wasn't assigned if this code isn't included

# check projection
# st_crs(cmu_bounds_albers) # epsg = 102008


# tabular data
# rainfall thresholds
rainfall_thresh_data <- read_csv(paste0(rainfall_thresh_tabular_data_input_path, "rainfall_thresholds.csv"))


# ---- 4b. load in latest least data (with dates) ----
# list files in lease_bounds_raw
# lease_files <- list.files(lease_data_spatial_input_path, pattern = "*.shp") # if there is a pop12 dataset there's a qpf dataset
# lease_files <- c(lease_files, "leases_20200401.shp") # to test with multiple

# pull out date strings
# lease_file_dates_str <- gsub("leases_", "", gsub(".shp", "", lease_files))

# convert date strings to dates
# lease_file_dates <- lubridate::ymd(lease_file_dates_str)

# get today's date
# today_date_uct <- lubridate::today(tzone = "UCT")

# calcualte difference
# diff_file_dates <- as.numeric(today_date_uct - lease_file_dates) # in days

# find position of smallest difference
# latest_date_uct <- lease_file_dates[diff_file_dates == min(diff_file_dates)]

# convert to string
# latest_date_uct_str <- strftime(latest_date_uct, format = "%Y%m%d")

# need if statement that if length(date_check) < 1 then don't run this script

# use latest date to read in most recent data
# lease_bounds_raw <- st_read(paste0(lease_raw_data_path, "leases_", latest_date_uct_str, ".shp"))

# check projection
# st_crs(lease_bounds_raw) # epsg = 2264

# sga data
# sga_bounds_albers <- st_read(paste0(sga_spatial_data_input_path, "sga_bounds_simple_albers.shp"))  %>%
#   st_set_crs(na_albers_epsg) # epsg code wasn't assigned if this code isn't included

# check projection
# st_crs(sga_bounds_albers) # epsg = 102008


# tabular data
# rainfall thresholds
# rainfall_thresh_data <- read_csv(paste0(rainfall_thresh_tabular_data_input_path, "rainfall_thresholds.csv"))


# ---- 5. project and tidy up lease data ----
lease_data_albers <- lease_bounds_raw %>%
  st_transform(crs = na_albers_epsg) %>% # project
  dplyr::select(lease_id = ProductNbr, # tidy
                owner = Owner,
                type = Type_,
                area_ac = A_Granted,
                status = Status,
                water_body = WB_Name,
                county = County)

# check projection
# st_crs(lease_data_albers)


# ---- 7. find centroids of leases ----
# calculate centroids of leases for map pins
lease_data_centroid_albers <- lease_data_albers %>%
  st_centroid()


# ---- 6. add sga and rainfall depths to lease data ----
# trim cmu data
cmu_bounds_albers_sel <- cmu_bounds_albers %>%
  dplyr::select(HA_CLASS, rain_in, rain_lab)

# trim rainfall threshold data
rainfall_thresh_data_sel <- rainfall_thresh_data %>%
  dplyr::select(HA_CLASS, grow_area)

# join lease and cmu data by geometry
# joining by cmu and not sga because each sga has mutiple cmu's within and therefore multiple rainfall thresholds
lease_data_centroid_albers_join <- lease_data_centroid_albers %>%
  st_intersection(cmu_bounds_albers_sel) %>%
  dplyr::left_join(rainfall_thresh_data_sel, by = "HA_CLASS") %>%
  dplyr::group_by(lease_id) %>%
  dplyr::slice(which.min(rain_in)) %>%
  #dplyr::group_by(lease_id, rain_in) %>%
  #dplyr::count() %>%
  dplyr::select(lease_id:county, grow_area, rain_in, rain_lab)

# NOTE!
# in the case that the centroid of the lease is at the edge of two growing areas then this code will take
# the minimum rainfall threshold, as of 20200716 it does not look like this is an issue but it cold be in
# the future
# for now there are ~ 20 (513-483 = 20) leases that have centroids which are not in cmu's and those are dropped

# save tabular data from lease_data_centroid_albers_join to the lease polygons
lease_data_centroids_join_no_geom <- lease_data_centroid_albers_join %>%
  st_drop_geometry() %>%
  dplyr::select(lease_id, grow_area:rain_lab)

# join to polygon dataset
lease_data_albers_join <- lease_data_albers %>%
  dplyr::left_join(lease_data_centroids_join_no_geom, by = "lease_id")

# resave centroids b/c lease_data_albers_join has full lease dataset
lease_data_centroids_albers_final <- lease_data_albers_join %>%
  st_centroid()


# ---- 8. project data ----
# project data and centroids to wgs84 projection
lease_data_wgs94 <- lease_data_albers_join %>%
  st_transform(crs = wgs84_epsg)
lease_data_centroid_wgs94 <- lease_data_centroids_albers_final %>%
  st_transform(crs = wgs84_epsg)

# keep a simplified copy of the centroids that can be pushed to the mysql db
lease_data_centroid_wgs94_simple <- lease_data_centroid_wgs94 %>%
  select(ncdmf_lease_id = lease_id,
         grow_area_name = grow_area,
         rainfall_thresh_in = rain_in)

# project data to geojson file type (need this for the web app)
lease_data_wgs94_geojson <- sf_geojson(lease_data_wgs94, atomise = FALSE, simplify = TRUE, digits = 5)
lease_data_centroid_wgs94_geojson <- sf_geojson(lease_data_centroid_wgs94, atomise = FALSE, simplify = TRUE, digits = 5)
lease_data_centroid_wgs94_simple_geojson <- sf_geojson(lease_data_centroid_wgs94_simple, atomise = FALSE, simplify = TRUE, digits = 5)


# ---- 9. export data ----
# export data as shape file for record keeping
# st_write(lease_data_albers_join, paste0(lease_data_spatial_output_path, "lease_bounds/lease_bounds_albers_", latest_date_uct_str, ".shp")) # includes date in file name
# st_write(lease_data_centroids_albers_final, paste0(lease_data_spatial_output_path, "lease_centroids/leases_centroids_albers_", latest_date_uct_str, ".shp")) # includes date in file name
st_write(lease_data_albers_join, paste0(lease_data_spatial_output_path, "lease_bounds/lease_bounds_albers.shp"), delete_layer = TRUE)
st_write(lease_data_centroids_albers_final, paste0(lease_data_spatial_output_path, "lease_centroids/leases_centroids_albers.shp"), delete_layer = TRUE)

# export data as geojson for web app
# write_file(lease_data_wgs94_geojson, paste0(lease_data_spatial_output_path, "lease_bounds/lease_bounds_wgs84_", latest_date_uct_str, ".geojson")) # includes date in file name
# write_file(lease_data_centroid_wgs94_geojson, paste0(lease_data_spatial_output_path, "lease_centroids/leases_centroids_wgs84_", latest_date_uct_str, ".geojson")) # includes date in file name
write_file(lease_data_wgs94_geojson, paste0(lease_data_spatial_output_path, "lease_bounds/lease_bounds_wgs84.geojson"))
write_file(lease_data_centroid_wgs94_geojson, paste0(lease_data_spatial_output_path, "lease_centroids/lease_centroids_wgs84.geojson"))
write_file(lease_data_centroid_wgs94_simple_geojson, paste0(lease_data_spatial_output_path, "lease_centroids/lease_centroids_simple_wgs84.geojson"))