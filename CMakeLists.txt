cmake_minimum_required(VERSION 3.15)
project(ssynth)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Python
find_package(Python COMPONENTS Interpreter Development REQUIRED)

# Find pybind11
find_package(pybind11 CONFIG REQUIRED)

# Find OpenMP
if(APPLE)
    execute_process(COMMAND brew --prefix libomp OUTPUT_VARIABLE OpenMP_PREFIX OUTPUT_STRIP_TRAILING_WHITESPACE)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -I${OpenMP_PREFIX}/include")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -I${OpenMP_PREFIX}/include")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -L${OpenMP_PREFIX}/lib -lomp")
endif()
find_package(OpenMP)
if(OpenMP_CXX_FOUND)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
endif()

# Wavetable Python module
pybind11_add_module(wavetable_cpp 
    Osc/bindings.cpp
    Osc/wavetable.cpp
)

if(OpenMP_CXX_FOUND)
    target_link_libraries(wavetable_cpp PRIVATE OpenMP::OpenMP_CXX)
    target_include_directories(wavetable_cpp PRIVATE ${OpenMP_CXX_INCLUDE_DIRS})
endif()

target_include_directories(wavetable_cpp PRIVATE Osc)

# Filter library
add_library(filter_raw SHARED
    Filter/Raw/low_and_high_filter.cpp
)

set_target_properties(filter_raw PROPERTIES
    PREFIX ""
    OUTPUT_NAME "filter_raw"
)
