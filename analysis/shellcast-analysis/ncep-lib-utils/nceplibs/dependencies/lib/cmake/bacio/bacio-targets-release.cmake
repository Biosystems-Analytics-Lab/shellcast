#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "bacio::bacio" for configuration "Release"
set_property(TARGET bacio::bacio APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(bacio::bacio PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C;Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libbacio.a"
  )

list(APPEND _cmake_import_check_targets bacio::bacio )
list(APPEND _cmake_import_check_files_for_bacio::bacio "${_IMPORT_PREFIX}/lib/libbacio.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
