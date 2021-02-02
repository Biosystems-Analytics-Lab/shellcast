
# ---- script header ----
# script name: ncdmf_tidy_cmu_bounds_script.R
# purpose of script: reformats the Conditional Management Units shapefile for downstream use
# author: sheila saia
# date created: 20201029
# email: ssaia@ncsu.edu


# ----
# notes:


# ----
# to do list


# ---- 1. load libraries -----
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
# data_base_path = "...analysis/data/" # set this and uncomment!
data_base_path = "/Users/sheila/Documents/github_ncsu/shellcast/analysis/data/"


# ---- 3. use base paths and define projections ----
# inputs
# path to cmu spatial inputs
cmu_spatial_data_input_path <- paste0(data_base_path, "spatial/inputs/ncdmf_data/cmu_bounds_raw/")

# path to rainfall threshold tabular inputs
rainfall_thresh_tabular_data_input_path <- paste0(data_base_path, "tabular/inputs/ncdmf_rainfall_thresholds/")

# outputs
# path to cmu spatial outputs
cmu_spatial_data_output_path <- paste0(data_base_path, "spatial/inputs/ncdmf_data/cmu_bounds/")

# path to rainfall threshold tabular outputs
rainfall_thresh_tabular_data_output_path <- paste0(data_base_path, "tabular/inputs/ncdmf_rainfall_thresholds/")

# projections
# define epsg of original dataset
nc_sp_epsg <- 6542
# https://epsg.io/6542

# define epsg and proj for CONUS Albers projection (projecting to this)
conus_albers_epsg <- 5070
# conus_albers_proj <- "+init=EPSG:5070"

# define egsp for wgs84
wgs84_epsg <- 4326


# ---- 4. initial processing of cmu bounds (with qgis notes too) ----
# cmu spatial data
cmu_bounds_raw <- st_read(paste0(cmu_spatial_data_input_path, "Conditional_Management_Units.shp")) %>%
  st_set_crs(nc_sp_epsg)

# st_crs(cmu_bounds_raw)

# clean up raw data and export for qgis processing
cmu_bounds_raw_albers <- cmu_bounds_raw %>%
  select(HA_CLASS, ClosingDat, OpeningDat, County, Comments, LABELS, Status, HA_STATUS) %>%
  group_by(HA_CLASS) %>%
  st_transform(conus_albers_epsg)

# export for qgis processing
st_write(cmu_bounds_raw_albers, paste0(cmu_spatial_data_input_path, "cmu_bounds_raw/cmu_bounds_raw_albers.shp"), delete_layer = TRUE)

# used "cmu_bounds_raw_albers.shp" to create "cmu_bounds_raw_valid_albers.shp"
# i used 'fix geometries' and 'check validity' tools in QGIS to fix invalid geometries
# i went in an manually checked cmu boundaries for cmu polygons that had multiple lines in the output
# and in some cases deleted or merged these using the editing tool in qgis
# i used the 'split multi-part feature into single part (interactive mode)"
# while editing to select the two polygons that i wanted to merge
# saved valid output to "cmu_bounds_valid_albers.shp"

# QGIS 'fix geometries' and 'check validity' tools version requirements
# QGIS version: 3.10.11-A Coruña
# QGIS code revision: d2171173e4
# Qt version: 5.12.3
# GDAL version: 2.4.1
# GEOS version: 3.7.2-CAPI-1.11.2 b55d2125
# PROJ version: Rel. 5.2.0, September 15th, 2018
# SQLITE version: 3.28.0


# ---- 5. load data ----

# cmu spatial data
cmu_bounds_raw_valid_albers <- st_read(paste0(cmu_spatial_data_input_path, "cmu_bounds_raw/cmu_bounds_raw_valid_albers.shp"))
# st_crs(cmu_bounds_raw_valid_albers) # looks ok, should be 5070

# check that removed duplicates
# length(cmu_bounds_raw_valid_albers$HA_CLASS)
# length(unique(cmu_bounds_raw_valid_albers$HA_CLASS))
# same lengths therefore checks!

# rainfall thresholds for cmu's
rainfall_thresholds_raw_tidy <- read_csv(paste0(rainfall_thresh_tabular_data_input_path, "rainfall_thresholds_raw_tidy.csv"), col_names = TRUE)

# sga key
sga_key <- read_csv(paste0(rainfall_thresh_tabular_data_input_path, "sga_key.csv"), col_names = TRUE)

# cmu to sga key
cmu_sga_key <- read_csv(paste0(rainfall_thresh_tabular_data_input_path, "cmu_sga_key.csv"), col_names = TRUE)


# ---- 6. join and clean up cmu bounds data ----
# select only columns we need
rain_thresh_data <- rainfall_thresholds_raw_tidy %>%
  dplyr::left_join(cmu_sga_key, by = "HA_CLASS") %>%
  dplyr::select(HA_CLASS, cmu_name, rain_in = rainfall_threshold_in, rain_lab = rainfall_threshold_class) %>%
  dplyr::distinct_all()

# length(unique(rain_thresh_data$HA_CLASS))
# 149 unique HA_CLASS values

# check unique HA_CLASS values in cmu_bounds_raw_valid_albers
# length(unique(cmu_bounds_raw_valid_albers$HA_CLASS))
# 149 unique HA_CLASS values! it's fine!

# join to cmu_bounds_raw_valid_albers
cmu_bounds_albers <- cmu_bounds_raw_valid_albers %>%
  dplyr::left_join(rain_thresh_data, by = "HA_CLASS") %>%
  dplyr::select(cmu_name:rain_lab)

# check that it joined
# names(cmu_bounds_albers)
# it checks!


# ---- 7. create geojson ----
# project to wgs84
cmu_bounds_wgs84 <- cmu_bounds_albers %>%
  st_buffer(dist = 1) %>% # distance units are meters, this will help with simplifying
  st_simplify(preserveTopology = TRUE, dTolerance = 100) %>%
  st_transform(crs = wgs84_epsg)
# st_crs(cmu_bounds_wgs84)
# it checks!

# create geojson
cmu_bounds_wgs84_geojson <- sf_geojson(cmu_bounds_wgs84, atomise = FALSE, simplify = TRUE, digits = 5)


# ---- 8. calculate simple buffer around cmu bounds ----
# cmu buffer
cmu_bounds_buffer_albers <- cmu_bounds_albers %>%
  st_convex_hull() %>% # for each cmu
  summarize() %>% # dissolve cmu bounds
  st_buffer(dist = 10000) %>% # buffer distance is in m so 10 * 1000m = 10km
  st_convex_hull() # simple buffer


# ---- 9. export data ----
# export cmu bounds
st_write(cmu_bounds_albers, paste0(cmu_spatial_data_output_path, "cmu_bounds_albers.shp"), delete_layer = TRUE)

# export cmu buffer
st_write(cmu_bounds_buffer_albers, paste0(cmu_spatial_data_output_path, "cmu_bounds_10kmbuf_albers.shp"), delete_layer = TRUE)

# export geojson
write_file(cmu_bounds_wgs84_geojson, paste0(cmu_spatial_data_output_path, "cmu_bounds_wgs84.geojson"))


