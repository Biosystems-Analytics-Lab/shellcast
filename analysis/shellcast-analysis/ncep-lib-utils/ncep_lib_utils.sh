#!/bin/sh

ROOT=$PWD
echo $ROOT
#brew install jasper
#brew install libpng
#brew install zlib
## BLAS and LAPACK
#brew install openblas
#export LDFLAGS="-L/usr/local/opt/openblas/lib"
#export CPPFLAGS="-I/usr/local/opt/openblas/include"
#export PKG_CONFIG_PATH="/usr/local/opt/openblas/lib/pkgconfig"
#If you installed this formula with the registration option (default), you'll
#need to manually remove [ODBC Driver 13 for SQL Server] section from
#odbcinst.ini after the formula is uninstalled. This can be done by executing
#the following command:
#    odbcinst -u -d -n "ODBC Driver 13 for SQL Server"
# after running above "ODBC Driver 13 for SQL Server usage count has been reduced to 5" shown

#mkdir $ROOT/nceplibs/dependencies

#cd $ROOT
#git clone https://github.com/NOAA-EMC/NCEPLIBS-bacio.git
#cd ./NCEPLIBS-bacio
#rm -rf build
#mkdir build && cd build
#cmake -DCMAKE_INSTALL_PREFIX=$ROOT'/nceplibs/dependencies' ..
#make -j4
#make install

#cd $ROOT
#git clone https://github.com/NOAA-EMC/NCEPLIBS-bufr.git
#cd ./NCEPLIBS-bufr
#rm -rf build
#mkdir build
#cd build
#cmake -DCMAKE_INSTALL_PREFIX=$ROOT'/nceplibs/dependencies' ..
#make -j4
#make install

#cd $ROOT
#git clone https://github.com/NOAA-EMC/NCEPLIBS-w3emc.git
#cd ./NCEPLIBS-w3emc
#rm -rf build
#mkdir build && cd build
#cmake -DCMAKE_INSTALL_PREFIX=$ROOT'/nceplibs/dependencies' ..
#make -j4
#make install

#cd $ROOT
#git clone https://github.com/NOAA-EMC/NCEPLIBS-sp.git
#cd ./NCEPLIBS-sp
#rm -rf build
#mkdir build && cd build
#cmake -DCMAKE_INSTALL_PREFIX=$ROOT'/nceplibs/dependencies' ..
#make -j4
#make install

#cd $ROOT
#git clone https://github.com/NOAA-EMC/NCEPLIBS-g2.git
#cd ./NCEPLIBS-g2
#rm -rf build
#mkdir build && cd build
#cmake -DCMAKE_INSTALL_PREFIX=$ROOT'/nceplibs/dependencies' ..
#make -j4
#make install

#cd $ROOT
#git clone https://github.com/NOAA-EMC/NCEPLIBS-ip.git
#cd ./NCEPLIBS-ip
#rm -rf build
#mkdir build && cd build
#cmake -DCMAKE_INSTALL_PREFIX=$ROOT'/nceplibs/dependencies' ..
#make -j4
#make install

# --- Notes for NCEPLIBS-grib_util ----
# Version 1.4
# make[2]: *** [src/tocgrib/tocgrib] Error 1
  #make[1]: *** [src/tocgrib/CMakeFiles/tocgrib.dir/all] Error 2
# I commented out lines that for "tocgrib" from  src/CMakeList.txt

cd $ROOT
git clone https://github.com/NOAA-EMC/NCEPLIBS-grib_util.git
cd  ./NCEPLIBS-grib_util
rm -rf build
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=$ROOT'/nceplibs' -DCMAKE_PREFIX_PATH=$ROOT'/nceplibs/dependencies' ..
make -j4
make install