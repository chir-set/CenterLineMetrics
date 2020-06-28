cmake_minimum_required(VERSION 3.13.4)

project(CentreLineMetrics)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/CentreLineMetrics")
set(EXTENSION_CATEGORY "Utilities")
set(EXTENSION_CONTRIBUTORS "SET (AnyWare Corp.)")
set(EXTENSION_DESCRIPTION "Get detailed metrics of a single CMTK centreline")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/CentreLineMetrics.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/CentreLineMetrics/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(CenterLineMetrics)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
