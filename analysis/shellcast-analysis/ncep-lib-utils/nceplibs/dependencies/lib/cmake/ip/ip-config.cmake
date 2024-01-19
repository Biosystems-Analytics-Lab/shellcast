
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

#  * ip::ip_4 - real32 library target
#  * ip::ip_8 - real64 library target
#  * ip::ip_d - mixed precision library target

# Include targets file.  This will create IMPORTED target ip
include("${CMAKE_CURRENT_LIST_DIR}/ip-targets.cmake")

include(CMakeFindDependencyMacro)

find_dependency(sp CONFIG)

if(OFF)
  find_dependency(OpenMP COMPONENTS Fortran)
endif()

# The target name needs to be one that's built, even if the dependent
# build does not use that version.
if(ON)
  set(precision 4)
elseif(ON)
  set(precision d)
elseif(OFF)
  set(precision 8)
endif()

get_target_property(ip_BUILD_TYPES ip::ip_${precision} IMPORTED_CONFIGURATIONS)

check_required_components("ip")

get_target_property(location ip::ip_${precision} LOCATION)
message(STATUS "Found ip: ${location} (found version \"4.4.0\")")
