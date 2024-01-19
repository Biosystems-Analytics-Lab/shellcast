
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

#g2-config.cmake
#
# Imported interface targets provided:
#  * g2::g2_4 - real32 library target
#  * g2::g2_d - mixed library target

# Include targets file.  This will create IMPORTED target g2
include("${CMAKE_CURRENT_LIST_DIR}/g2-targets.cmake")

include(CMakeFindDependencyMacro)

find_dependency(PNG)

get_target_property(g2_BUILD_TYPES g2::g2_4 IMPORTED_CONFIGURATIONS)

check_required_components("g2")

get_target_property(location g2::g2_4 LOCATION)
message(STATUS "Found g2: ${location} (found version \"3.4.8\")")
