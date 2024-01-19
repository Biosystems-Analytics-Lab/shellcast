
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

#  * sp::sp_4 - real32 library target
#  * sp::sp_8 - real64 library target
#  * sp::sp_d - mixed precision library target

# Include targets file.  This will create IMPORTED target sp
include("${CMAKE_CURRENT_LIST_DIR}/sp-targets.cmake")

include(CMakeFindDependencyMacro)

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

get_target_property(sp_BUILD_TYPES sp::sp_${precision} IMPORTED_CONFIGURATIONS)

check_required_components("sp")

get_target_property(location sp::sp_${precision} LOCATION)
message(STATUS "Found sp: ${location} (found version \"2.5.0\")")
