#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "sp::sp_4" for configuration "Release"
set_property(TARGET sp::sp_4 APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(sp::sp_4 PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libsp_4.a"
  )

list(APPEND _cmake_import_check_targets sp::sp_4 )
list(APPEND _cmake_import_check_files_for_sp::sp_4 "${_IMPORT_PREFIX}/lib/libsp_4.a" )

# Import target "sp::sp_d" for configuration "Release"
set_property(TARGET sp::sp_d APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(sp::sp_d PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libsp_d.a"
  )

list(APPEND _cmake_import_check_targets sp::sp_d )
list(APPEND _cmake_import_check_files_for_sp::sp_d "${_IMPORT_PREFIX}/lib/libsp_d.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
