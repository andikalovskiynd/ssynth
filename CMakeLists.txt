cmake_minimum_required(VERSION 3.15)
project(ssynth CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_INTERPROCEDURAL_OPTIMIZATION OFF)

if(APPLE)
    execute_process(COMMAND brew --prefix libomp OUTPUT_VARIABLE OpenMP_PREFIX OUTPUT_STRIP_TRAILING_WHITESPACE)
    execute_process(COMMAND brew --prefix fftw OUTPUT_VARIABLE FFTW_PREFIX OUTPUT_STRIP_TRAILING_WHITESPACE)
    
    list(APPEND CMAKE_PREFIX_PATH "${OpenMP_PREFIX}")
    list(APPEND CMAKE_PREFIX_PATH "${FFTW_PREFIX}")

    set(OPENMP_DIR "${OpenMP_PREFIX}/lib")
    set(OPENMP_INCLUDE_DIR "${OpenMP_PREFIX}/include")
    set(FFTW_DIR "${FFTW_PREFIX}/lib")
    
    set(CMAKE_MACOSX_RPATH 1)
    set(INSTALL_RPATH_PATHS "${OPENMP_DIR};${FFTW_DIR};@rpath")
endif()

find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG REQUIRED)
find_package(OpenMP REQUIRED)

find_path(FFTW3_INCLUDE_DIR NAMES fftw3.h PATHS ${FFTW_PREFIX}/include)

find_library(FFTW3_THREAD_LIBRARY NAMES fftw3_threads PATHS ${FFTW_PREFIX}/lib)
find_library(FFTW3_MAIN_LIBRARY NAMES fftw3 PATHS ${FFTW_PREFIX}/lib)

if (FFTW3_THREAD_LIBRARY AND FFTW3_MAIN_LIBRARY)
    set(FFTW3_LIBRARIES ${FFTW3_THREAD_LIBRARY} ${FFTW3_MAIN_LIBRARY})
else()
    message(FATAL_ERROR "FFTW3 libraries (threads/main) not found. Ensure 'brew install fftw' was run.")
endif()


pybind11_add_module(wavetable_cpp
    Osc/bindings.cpp
    Osc/wavetable.cpp
)

target_include_directories(wavetable_cpp PRIVATE Osc ${OPENMP_INCLUDE_DIR})

if(APPLE)
    set_property(TARGET wavetable_cpp PROPERTY INSTALL_RPATH ${INSTALL_RPATH_PATHS})
    target_link_libraries(wavetable_cpp PRIVATE OpenMP::OpenMP_CXX Python::Module)
endif()

pybind11_add_module(spectrogram_cpp
    gui/visual/spectrogram/bindings_spectrogram.cpp
    gui/visual/spectrogram/fftw_setup.cpp
    gui/visual/spectrogram/spectrogram_vis.cpp
)

target_include_directories(spectrogram_cpp PRIVATE 
    gui/visual/spectrogram 
    ${OPENMP_INCLUDE_DIR}
    ${FFTW3_INCLUDE_DIR}
)

if(APPLE)
    set_property(TARGET spectrogram_cpp PROPERTY INSTALL_RPATH ${INSTALL_RPATH_PATHS})
    
    target_link_libraries(spectrogram_cpp PRIVATE 
        Python::Module
        ${FFTW3_LIBRARIES}
        OpenMP::OpenMP_CXX
    )
endif()

add_library(filter_raw SHARED
    Filter/Raw/low_and_high_filter.cpp
)

set_target_properties(filter_raw PROPERTIES
    PREFIX ""
    OUTPUT_NAME "filter_raw"
)

if(APPLE)
    set_property(TARGET filter_raw PROPERTY INSTALL_RPATH ${INSTALL_RPATH_PATHS})
    target_link_libraries(filter_raw PRIVATE OpenMP::OpenMP_CXX)
endif()

target_include_directories(filter_raw PRIVATE Filter/Raw)