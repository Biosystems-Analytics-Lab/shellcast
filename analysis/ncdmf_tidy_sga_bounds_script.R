
# ---- script header ----
# script name: ncdmf_tidy_sga_bounds_script.R
# purpose of script: wrangling nc dmf shellfish growing area (sga) data
# author: sheila saia
# date created: 20201101
# email: ssaia@ncsu.edu


# ---- notes ----
# notes:
 

# ---- to do ----
# to do list
# TODO change grow_area to sga_name throughout and re-export

# ---- 1. load libraries ----
# packages
packages <- c("tidyverse", "sf", "geojsonsf", "here")

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
# data_base_path = "/Users/sheila/Documents/github_ncsu/shellcast/analysis/data/"
data_base_path = here::here("data")

# ---- 3. use base paths and define projections ----
# inputs
# path to sga spatial inputs (raw data)
sga_spatial_data_input_path <- paste0(data_base_path, "/spatial/inputs/ncdmf_data/sga_bounds_raw/")

# outputs
# path to sga spatial outputs
sga_spatial_data_output_path <- paste0(data_base_path, "/spatial/inputs/ncdmf_data/sga_bounds/")

# projections
# define epsg and proj for CONUS Albers projection (projecting to this)
conus_albers_epsg <- 5070
# conus_albers_proj <- "+init=EPSG:5070"

# define egsp for wgs84
wgs84_epsg <- 4326


# ---- 2. load data ----
# shellfish growing area data
sga_bounds_raw <- st_read(paste0(sga_spatial_data_input_path, "SGA_Current_Classifications.shp"))

# columns
# OBJECTID_1, OBJECTID_2, OBJECTID, OBJECTID_3, SGA_INDEX - not really sure what these are but think these are all artifacts from ArcGIS
# REGION = region of coast (central, north, south) 
# GROW_AREA = growing area (GA) code is a two digits code (e.g., letter + number like A1), first digit (letter) is HA_AREA, second digist (number) is HA_SUBAREA
# DSHA_NAME = full written out name for location (e.g., Calabash Area)
# DSHA_ID = like GA code but has dash between digits (e.g., A-1)
# DSHA_AREA = first digit of GA (e.g., letter like A)
# DSHA_CODE = like GA code but lower case letter (e.g., a1)
# DSHA_LABEL = same as DSHA_ID
# HA_CLASS = describes status of GA (restricted, conditionally approved - open, conditionally approved - closed, approved)
# HA_CLASSID = shorter version of HA_CLASS (R, CA-O, CA-C, APP)
# HA_NAME = full written out name for location given by HA_CODE (e.g., Calabash/Sunset Beach/Boneparte Creek Area)
# HA_NAMEID = like HA_CODE but with dashes and spaces (e.g., A-1 CA-C 1)
# HA_STATUS = GA status (open or closed)
# HA_AREA = first digit letter of GA (e.g., A), A through I
# HA_SUBAREA = second digit number of GA (e.g., 1)
# HA_CODE = like GA code but has additional information including status and subsub area (e.g., a1cac1)
# HA_LABEL = same as HA_NAMEID
# MAP_NAME = contributing watershed/river (61 unique values)
# MAP_NUMBER = map number corresponding to MAP_NAME (51 unique values)
# MAP_ID = number from MAP_NUMBER and letter (?)
# COUNTY = county
# JURISDCTN = jursdiction (WRC, DMF)
# WATER_DES = inland, coastal, joint, land
# SURFACE = canal, land, water, mhw (?)
# RELAY = ? (NA, N/A, YES, LAND, NO)
# CREATOR = who created the area/data
# CREATED = date of creation of the area/data?
# UPDATED = date the area/data was updated?
# ACRES = area of grow area in acres
# SQ_MILES = area of grow area in sqare miles
# SHAPE_Leng = ?
# Shape_Le_1 = ?
# GlobalID = ?
# SHAPE_Le_2 =? 
# GlobalID_2 = ?
# Shape__Are = ?
# Shape__Len = ?
# GlobalID_3 = ?
# Shape__A_1 = ?
# Shape__L_1 = ?

# other observations
# 1. as far as I can tell DSHA_CODE, HA_NAMEID, HA_AREA, HA_SUBAREA all have similar info to GROW_AREA
# 2. HA_LABEL,DSHA_LABEL, and MAP_ID have a lot of NA values (not filled in values) so might not be very helpful
# 3. HA_CODE has a third digit (i.e., letters) that GROW_AREA does not have - will need this
# 4. DSHA_NAME and HA_NAME are similar but looks like HA_NAME has more detail (going along with HA_NAMEID and HA_CODE)
# 5. some of the MAP_NAME and MAP_NUMBER columns are NA values
# 6. what's the details with the UPDATED column?
# 7. sometimes HA_AREA and HA_SUBAREA are not given even though GROW_AREA is
# 8. HA_AREA and HA_SUBAREA are never given if GROW_AREA is not given - basically they're not too helpful


# ---- 3. initial tidy sga bounds ----
# check crs
st_crs(sga_bounds_raw)
# it's not projected (wgs 84)

# initial tidy and project
sga_bounds_raw_albers <- sga_bounds_raw %>%
  select(OBJECTID_1, REGION:DSHA_NAME, HA_NAME, HA_CLASS, HA_CLASSID, HA_STATUS, MAP_NAME:SQ_MILES) %>%
  filter(is.na(GROW_AREA) != TRUE) %>% # ignore rows where GROW_AREA = NULL
  st_transform(conus_albers_epsg) # project

# check crs
st_crs(sga_bounds_raw_albers)

# export to fix geometries in QGIS using 'fix geometries' and 'check validity' tools
st_write(sga_bounds_raw_albers, paste0(sga_spatial_data_input_path, "sga_bounds_raw_albers.shp"), delete_layer = TRUE)

# used "sga_bounds_raw_albers.shp" to create "sga_bounds_raw_valid_albers.shp"
# i used 'fix geometries' and 'check validity' tools in QGIS to fix invalid geometries

# QGIS 'fix geometries' and 'check validity' tools version requirements
# QGIS version: 3.10.11-A Coruña
# QGIS code revision: d2171173e4
# Qt version: 5.12.3
# GDAL version: 2.4.1
# GEOS version: 3.7.2-CAPI-1.11.2 b55d2125
# PROJ version: Rel. 5.2.0, September 15th, 2018
# SQLITE version: 3.28.0

# run these two tools and fixed all invalid polygons
# saved fixed (and checked) file in QGIS as "sga_bounds_raw_valid_albers.shp" in the sga_bounds_raw directory


# ---- 4. load data ----
# shellfish growing area data that's been initially cleaned (see ncdmf_init_tidy_sga_bounds_script.R)
sga_bounds_raw_valid_albers <- st_read(paste0(sga_spatial_data_input_path, "sga_bounds_raw_valid_albers.shp"))

# names(sga_bounds_raw_valid_albers)

# columns
# OBJECTID_1 - not really sure what these are but think these are all artifacts from ArcGIS
# REGION = region of coast (central, north, south) 
# GROW_AREA = growing area (GA) code is a two digits code (e.g., letter + number like A1), first digit (letter) is HA_AREA, second digist (number) is HA_SUBAREA
# DSHA_NAME = full written out name for location (e.g., Calabash Area)
# HA_NAME = full written out name for location given by HA_CODE (e.g., Calabash/Sunset Beach/Boneparte Creek Area)
# HA_CLASS = describes status of GA (restricted, conditionally approved - open, conditionally approved - closed, approved)
# HA_CLASSID = shorter version of HA_CLASS (R, CA-O, CA-C, APP)
# HA_STATUS = GA status (open or closed)
# MAP_NAME = contributing watershed/river (61 unique values)
# MAP_NUMBER = map number corresponding to MAP_NAME (51 unique values)
# MAP_ID = number from MAP_NUMBER and letter (?)
# COUNTY = county
# JURISDCTN = jursdiction (WRC, DMF)
# WATER_DES = inland, coastal, joint, land
# SURFACE = canal, land, water, mhw (?)
# RELAY = ? (NA, N/A, YES, LAND, NO)
# CREATOR = who created the area/data
# CREATED = date of creation of the area/data?
# UPDATED = date the area/data was updated?
# ACRES = area of grow area in acres
# SQ_MILES = area of grow area in sqare miles


# ---- 5. tidy sga bounds attribute data ----
# tidy data
sga_bounds_albers <- sga_bounds_raw_valid_albers %>%
  dplyr::mutate(ga_class = if_else(HA_CLASSID == "APP", "approved",
                                          if_else(HA_CLASSID == "CA-O" | HA_CLASSID == "CA-C", "cond_approved",
                                                  if_else(HA_CLASSID == "CSHA-P", "prohibited", "restricted"))), # don't care if they're open or closed, just if they are approved, conditionally approve, prohibited, or restricted
                grow_area_trim = str_trim(GROW_AREA, side = "both"),
                ha_area_fix = str_to_upper(str_sub(grow_area_trim, start = 1, end = 1)), # original HA_AREA has some NAs so generate from scratch
                ha_subarea_fix = str_pad(str_sub(grow_area_trim, start = 2, end = -1), 2, side = "left", "0"), # original HA_SUBAREA has some NAs so generate from scratch
                grow_area = paste0(ha_area_fix, ha_subarea_fix), 
                ga_name = if_else(is.na(HA_NAME) == TRUE, as.character(DSHA_NAME), as.character(HA_NAME))) %>% # if there's no name use general name (i.e., DSHA_NAME)
  dplyr::select(grow_area,
                ga_class, 
                region = REGION, 
                dsha_name = DSHA_NAME, 
                ha_name = HA_NAME,
                ga_name,
                map_name = MAP_NAME, 
                county = COUNTY, 
                jursidctn = JURISDCTN,
                water_desc = WATER_DES,
                surface = SURFACE,
                creator = CREATOR) %>% # reorder columns
  dplyr::arrange(grow_area, ga_class, ha_name) %>%
  dplyr::mutate(row_id = seq(1:7033))

# rows where ga_name is NA
sga_bounds_albers$row_id[is.na(sga_bounds_albers$ga_name) == TRUE]
# row 5399 is only one

# filter out row 5399 and fix (only row with NULL ga_name)
sga_bounds_albers_row_5399_fix <- sga_bounds_albers %>%
  dplyr::filter(row_id == 5399)
sga_bounds_albers_row_5399_fix$dsha_name <- "North River"
sga_bounds_albers_row_5399_fix$ga_name <- "North River"

# take out and add fixed version of row 5399 back and project
sga_bounds_albers <- sga_bounds_albers %>%
  dplyr::filter(row_id != 5399) %>%
  rbind(sga_bounds_albers_row_5399_fix) %>%
  dplyr::select(-row_id)
# names(sga_bounds_albers)

# check validity of polygons (shouldn't be a problem but just in case)
sga_bounds_albers_check <- sga_bounds_albers %>%
  dplyr::mutate(polygon_valid_check = st_is_valid(sga_bounds_albers))
# names(sga_bounds_albers_check)

# look at invalid sga's
sga_bounds_albers_invalid_tabular <- sga_bounds_albers_check %>% 
  st_drop_geometry() %>%
  dplyr::filter(polygon_valid_check == FALSE)
# there should be no invalid polygons which is true, so, check!


# ---- 6. tidy sga boundaries by sga (simple boundary line) ----
# summarize boundaries (equivalent to spatial dissolve)
sga_bounds_simple_albers <- sga_bounds_albers %>%
  group_by(grow_area) %>% # group by sga name
  summarize() %>%
  st_buffer(dist = 1) %>% # distance units are meters
  st_simplify(preserveTopology = TRUE, dTolerance = 100) # in units of meters
# NOTE: this takes a while to run! (~4 min)


# ---- 7. calculate simple buffer around sga bounds ----
# sga buffer
sga_bounds_buffer_albers <- sga_bounds_simple_albers %>%
  st_convex_hull() %>% # simple buffer for each sga
  summarize() %>% # dissolve sga bounds
  st_buffer(dist = 10000) %>% # buffer distance is in m so 10 * 1000m = 10km
  st_convex_hull() # simple buffer for all sgas


# ---- 8. tidy sga boundaries by sga and class ----
# summarize boundaries (equivalent to spatial dissolve)
sga_bounds_class_albers <- sga_bounds_albers %>%
  dplyr::group_by(grow_area, ga_class, ga_name) %>% # group by sga name and class
  dplyr::summarize() %>%
  st_buffer(dist = 1) # buffer 1 m



# ---- 7. export data ----
# export tidy sga bounds
st_write(sga_bounds_albers, paste0(sga_spatial_data_output_path, "sga_bounds_albers.shp"), delete_layer = TRUE)

# export sga simple bounds
st_write(sga_bounds_simple_albers, paste0(sga_spatial_data_output_path, "sga_bounds_simple_albers.shp"), delete_layer = TRUE)

# export sga buffer bounds
st_write(sga_bounds_buffer_albers, paste0(sga_spatial_data_output_path, "sga_bounds_10kmbuf_albers.shp"), delete_layer = TRUE)

# export sga class bounds
st_write(sga_bounds_class_albers, paste0(sga_spatial_data_output_path, "sga_bounds_class_albers.shp"), delete_layer = TRUE)

# save as wgs84 for geojson
# sga_bounds_simple_wgs84 <- sga_bounds_simple_albers %>%
#   st_transform(wgs84_epsg)

# simplify further to reduce geoJSON size for the web app
# sga_bounds_simple_wgs84_geojson <- sf_geojson(sga_bounds_simple_wgs84, atomise = FALSE, simplify = TRUE, digits = 5)

# export geoJSON
# write_file(sga_bounds_simple_wgs84_geojson, paste0(sga_spatial_data_output_path, "sga_bounds_simple_wgs84.geojson"))
