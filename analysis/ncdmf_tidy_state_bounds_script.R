# ---- script header ----
# script name: ncdmf_tidy_state_bounds_script.R
# purpose of script: tidying regional and state bounds for later calcs
# author: sheila saia
# date created: 20200604
# email: ssaia@ncsu.edu


# ---- notes ----
# notes:


# ---- to do ----
# to do list


# ---- 1. load libraries ----=
# load libraries
library(tidyverse)
library(sf)


# ---- 2. define base paths ----
# base path to data
# data_base_path = "...analysis/data/" # set this and uncomment!
data_base_path = "/Users/sheila/Documents/bae_shellcast_project/shellcast_analysis/web_app_data/"


# ---- 3. use base paths and define projections ----
# path to state bounds spatial inputs
state_bounds_spatial_data_input_path <- paste0(data_base_path, "spatial/inputs/state_bounds_data/state_bounds_raw/")

# path to state bounds spatial outputs
state_bounds_spatial_data_output_path <- paste0(data_base_path, "spatial/inputs/state_bounds_data/state_bounds/")

# define epsg and proj4 for N. America Albers projection (projecting to this)
na_albers_proj4 <- "+proj=aea +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs"
na_albers_epsg <- 102008

# define wgs 84 projection
wgs84_epsg <- 4326


# ---- 3. load data ----
# state boundaries spatial data
state_bounds_raw <- st_read(paste0(state_bounds_spatial_data_input_path, "state_bounds.shp"))


# ---- 4. check spatial data projections and project ----
# check state bounds
st_crs(state_bounds_raw)
# epsg 5070 (albers conic equal area)

# project to na albers
state_bounds_albers <- state_bounds_raw %>%
  dplyr::select(OBJECTID:NAME) %>%
  st_transform(crs = na_albers_epsg)
# st_crs(state_bounds_albers)
# it checks!

# project to wgs84
state_bounds_wgs84 <- state_bounds_raw %>%
  dplyr::select(OBJECTID:NAME) %>%
  st_transform(crs = wgs84_epsg)
# st_crs(state_bounds_wgs84)
# it checks!

# export data
st_write(state_bounds_albers, paste0(state_bounds_spatial_data_output_path, "state_bounds_albers.shp"), delete_layer = TRUE)
st_write(state_bounds_wgs84, paste0(state_bounds_spatial_data_output_path, "state_bounds_wgs84.shp"), delete_layer = TRUE)


# ---- 5. select only nc bounds and buffer ----
# select and keep only geometry
nc_bounds_geom_albers <- state_bounds_albers %>%
  filter(NAME == "North Carolina") %>%
  st_geometry() %>%
  st_simplify()

# keep a copy projected to wgs84 too
nc_bounds_geom_wgs84 <- nc_bounds_geom_albers %>%
  st_transform(crs = wgs84_epsg)

# export
# st_write(nc_bounds_geom_albers, paste0(state_bounds_spatial_data_output_path, "nc_bounds_albers.shp"), delete_layer = TRUE)
# st_write(nc_bounds_geom_wgs84, paste0(state_bounds_spatial_data_output_path, "nc_bounds_wgs84.shp"), delete_layer = TRUE)


# ---- 6. buffer bounds ----

# buffer 5 km
# nc_bounds_5kmbuf_albers <- nc_bounds_geom_albers %>%
#  st_buffer(dist = 5000) # distance is in m so 5 * 1000m = 5km

# buffer 10 km
nc_bounds_10kmbuf_albers <- nc_bounds_geom_albers %>%
  st_buffer(dist = 10000) # distance is in m so 10 * 1000m = 10km

# save a copy projected to wgs84
nc_bounds_10kmbuf_wgs84 <- nc_bounds_10kmbuf_albers %>%
  st_transform(crs = wgs84_epsg)

# export
# st_write(nc_bounds_5kmbuf_albers, paste0(state_bounds_spatial_data_output_path, "nc_bounds_5kmbuf_albers.shp"), delete_layer = TRUE)
st_write(nc_bounds_10kmbuf_albers, paste0(state_bounds_spatial_data_output_path, "nc_bounds_10kmbuf_albers.shp"), delete_layer = TRUE)
st_write(nc_bounds_10kmbuf_wgs84, paste0(state_bounds_spatial_data_output_path, "nc_bounds_10kmbuf_wgs84.shp"), delete_layer = TRUE)

