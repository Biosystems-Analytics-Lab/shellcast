#!/bin/sh
ROOT=$PWD

brew install jasper
brew install libpng
brew install zlib

git clone https://github.com/NOAA-EMC/NCEPLIBS-bacio.git
cd ./NCEPLIBS-bacio
rm -rf build
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX=$ROOT'/nceplibs/dependencies' ..
make -j4
make install

git clone https://github.com/NOAA-EMC/NCEPLIBS-bufr.git
cd $ROOT'/NCEPLIBS-bufr'
rm -rf build
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX=$ROOT'/nceplibs/dependencies' ..
make -j4
make install

git clone https://github.com/NOAA-EMC/NCEPLIBS-w3emc.git
cd $ROOT'/NCEPLIBS-w3emc'
rm -rf build
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=$ROOT'/nceplibs/dependencies' ..
make -j4
make install

git clone https://github.com/NOAA-EMC/NCEPLIBS-sp.git
cd $ROOT'/NCEPLIBS-sp'
rm -rf build
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=$ROOT'/nceplibs/dependencies' ..
make -j4
make install

git clone https://github.com/NOAA-EMC/NCEPLIBS-g2.git
cd $ROOT'/NCEPLIBS-g2'
rm -rf build
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=$ROOT'/nceplibs/dependencies' ..
make -j4
make install

git clone https://github.com/NOAA-EMC/NCEPLIBS-ip.git
cd $ROOT'/NCEPLIBS-ip'
rm -rf build
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=$ROOT'/nceplibs/dependencies' ..
make -j4
make install

# --- Notes for NCEPLIBS-grib_util ----
# Version 1.3 has error
# make[2]: *** [src/tocgrib/tocgrib] Error 1
  #make[1]: *** [src/tocgrib/CMakeFiles/tocgrib.dir/all] Error 2
# I commented out lines that for "toc" from  src/CMakeList.txt

git clone https://github.com/NOAA-EMC/NCEPLIBS-grib_util.git
cd $ROOT'/NCEPLIBS-grib_util'
rm -rf build
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=$ROOT'/nceplibs' -DCMAKE_PREFIX_PATH=$ROOT'/nceplibs/dependencies' ..
make -j4
make install