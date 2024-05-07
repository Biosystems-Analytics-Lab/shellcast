#!/bin/sh
CUR_DIR="${PWD%/*}"
ROOT="$(dirname "$CUR_DIR")"
echo $ROOT
RAW_DATA_DIR=$ROOT'/data/tp/raw'
INTERMEDIATE_DIR=$ROOT'/data/tp/fl/intermediate'
TP_OUTPUTS_DIR=$ROOT'/data/tp/fl/outputs'
INTERMEDIATE_PROC_DIR=$INTERMEDIATE_DIR'/procs'
CNV_GRIB2_DIR=$INTERMEDIATE_DIR'/cnvgrib2'
NCEPLIB=$ROOT'/ncep-lib-utils/nceplibs/bin'

rm -rf $CNV_GRIB2_DIR
mkdir $CNV_GRIB2_DIR

# Convert GRIB1  to GRIB2
counter=0
raw_gribs=`ls $RAW_DATA_DIR/*.grb`
for grib in $raw_gribs
do
  fname=`basename $grib`
  `$NCEPLIB/cnvgrib -g12 $grib $CNV_GRIB2_DIR/$fname`
  counter=$((counter+1))
done

# ----- Clean directory -----
rm -f -R $TP_OUTPUTS_DIR
mkdir $TP_OUTPUTS_DIR
chmod -R 777 $TP_OUTPUTS_DIR
rm -f -R $INTERMEDIATE_PROC_DIR
mkdir $INTERMEDIATE_PROC_DIR
cd $INTERMEDIATE_PROC_DIR

# ----- Process data -----
# Merge
cdo -O -mergetime $CNV_GRIB2_DIR'/*grb' all.grb
# Reproject to WGS84 from Polarstereographic projection
gdalwarp -t_srs EPSG:4326 all.grb proj.grb
# Crop AOI
wgrib2 proj.grb -small_grib -88:-80 24:31 small.grb
# Convert GRIB to NetCDF
cdo -O -f nc copy small.grb small.nc
# Convert data to inches
cdo -O -b f32 expr,"tp_1h=param8.1.0*0.03937" small.nc calc.nc
# Set attribute unit
cdo -O setattribute,"tp_1h@units=inches" calc.nc unit.nc
# Computes the accumulation of the given variable over time
cdo -O timcumsum unit.nc timcumsum.nc

# ----- Convert to TIFF -----
for ((i=24; i<=$counter; i+=24 ));
  do
    # Select 24, 48, 72, 96, and 120 hours accumulation data
    cdo -O seltimestep,$i timcumsum.nc 'tp_'$i'h'.nc
    outfile=$TP_OUTPUTS_DIR'/tp_'$i'h.tif'
    # Convert it to TIFF
    gdalwarp -of GTiff -t_srs EPSG:4326 'tp_'$i'h'.nc $outfile
done

