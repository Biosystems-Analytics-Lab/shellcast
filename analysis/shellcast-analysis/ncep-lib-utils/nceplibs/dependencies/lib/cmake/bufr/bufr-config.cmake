
####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was PackageConfig.cmake.in                            ########

get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../../../" ABSOLUTE)

macro(set_and_check _var _file)
  set(${_var} "${_file}")
  if(NOT EXISTS "${_file}")
    message(FATAL_ERROR "File or directory ${_file} referenced by variable ${_var} does not exist !")
  endif()
endmacro()

macro(check_required_components _NAME)
  foreach(comp ${${_NAME}_FIND_COMPONENTS})
    if(NOT ${_NAME}_${comp}_FOUND)
      if(${_NAME}_FIND_REQUIRED_${comp})
        set(${_NAME}_FOUND FALSE)
      endif()
    endif()
  endforeach()
endmacro()

####################################################################################

#  * bufr::bufr_4    - real32 library target
#  * bufr::bufr_8    - real64 library target
#  * bufr::bufr_d    - mixed library target

# Include targets file.  This will create IMPORTED target bufr
include("${CMAKE_CURRENT_LIST_DIR}/bufr-targets.cmake")

# Get the build type from real32 library target with dyanmic allocation
get_target_property(bufr_BUILD_TYPES bufr::bufr_4 IMPORTED_CONFIGURATIONS)

check_required_components("bufr")

set(bufr_TABLES_DIR "/Users/makiko/CGAProjects/NCSUGitHubProjects/shellcast/analysis/shellcast-analysis/ncep-lib-utils/nceplibs/dependencies/tables")

get_target_property(location bufr::bufr_4 LOCATION)
message(STATUS "Found bufr: ${location} (found version \"12.0.1\")")
