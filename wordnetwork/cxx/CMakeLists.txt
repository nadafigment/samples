cmake_minimum_required (VERSION 2.6)
project (wordnetwork)
include_directories ("${CMAKE_CURRENT_SOURCE_DIR}")
add_executable (wordnetwork word.cxx wordnetwork.cxx)
