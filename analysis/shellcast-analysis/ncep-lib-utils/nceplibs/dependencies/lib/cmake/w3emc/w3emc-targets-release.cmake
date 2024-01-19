#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "w3emc::w3emc_4" for configuration "Release"
set_property(TARGET w3emc::w3emc_4 APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(w3emc::w3emc_4 PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C;Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libw3emc_4.a"
  )

list(APPEND _cmake_import_check_targets w3emc::w3emc_4 )
list(APPEND _cmake_import_check_files_for_w3emc::w3emc_4 "${_IMPORT_PREFIX}/lib/libw3emc_4.a" )

# Import target "w3emc::w3emc_d" for configuration "Release"
set_property(TARGET w3emc::w3emc_d APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(w3emc::w3emc_d PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C;Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libw3emc_d.a"
  )

list(APPEND _cmake_import_check_targets w3emc::w3emc_d )
list(APPEND _cmake_import_check_files_for_w3emc::w3emc_d "${_IMPORT_PREFIX}/lib/libw3emc_d.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
