#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "ip::ip_4" for configuration "Release"
set_property(TARGET ip::ip_4 APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(ip::ip_4 PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libip_4.a"
  )

list(APPEND _cmake_import_check_targets ip::ip_4 )
list(APPEND _cmake_import_check_files_for_ip::ip_4 "${_IMPORT_PREFIX}/lib/libip_4.a" )

# Import target "ip::ip_d" for configuration "Release"
set_property(TARGET ip::ip_d APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(ip::ip_d PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libip_d.a"
  )

list(APPEND _cmake_import_check_targets ip::ip_d )
list(APPEND _cmake_import_check_files_for_ip::ip_d "${_IMPORT_PREFIX}/lib/libip_d.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
