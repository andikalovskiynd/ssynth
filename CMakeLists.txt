cmake_minimum_required(VERSION 3.15)
project(ssynth CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_INTERPROCEDURAL_OPTIMIZATION OFF)

# ==========================================
# =       MACOS / HOMEBREW PATHS           =
# ==========================================
if(APPLE)
    execute_process(COMMAND brew --prefix libomp OUTPUT_VARIABLE OpenMP_PREFIX OUTPUT_STRIP_TRAILING_WHITESPACE)
    execute_process(COMMAND brew --prefix fftw OUTPUT_VARIABLE FFTW_PREFIX OUTPUT_STRIP_TRAILING_WHITESPACE)
    
    list(APPEND CMAKE_PREFIX_PATH "${OpenMP_PREFIX}")
    list(APPEND CMAKE_PREFIX_PATH "${FFTW_PREFIX}")

    set(OPENMP_DIR "${OpenMP_PREFIX}/lib")
    set(OPENMP_INCLUDE_DIR "${OpenMP_PREFIX}/include")
    
    set(FFTW_DIR "${FFTW_PREFIX}/lib")
    set(FFTW_INCLUDE_DIR "${FFTW_PREFIX}/include")
    
    set(CMAKE_MACOSX_RPATH 1)
    set(INSTALL_RPATH_PATHS "${OPENMP_DIR};${FFTW_DIR};@rpath")
endif()

# ==========================================
# =           DEPENDENCIES                 =
# ==========================================

find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG REQUIRED)
find_package(OpenMP REQUIRED)

find_path(FFTW3_INCLUDE_DIR NAMES fftw3.h PATHS ${FFTW_INCLUDE_DIR})

find_library(FFTW3F_MAIN_LIBRARY NAMES fftw3f PATHS ${FFTW_DIR})
find_library(FFTW3F_THREAD_LIBRARY NAMES fftw3f_threads fftw3f_omp PATHS ${FFTW_DIR})

if (FFTW3F_MAIN_LIBRARY)
    message(STATUS "Found FFTW3F (Float): ${FFTW3F_MAIN_LIBRARY}")
    set(FFTW_LIBRARIES ${FFTW3F_MAIN_LIBRARY})
    
    if (FFTW3F_THREAD_LIBRARY)
        list(APPEND FFTW_LIBRARIES ${FFTW3F_THREAD_LIBRARY})
    endif()
else()
    message(FATAL_ERROR "FFTW3F (Float version) library not found. Ensure 'brew install fftw' is run and float libs are present.")
endif()


# ==========================================
# =           MAIN ENGINE TARGET           =
# ==========================================

set(ENGINE_SOURCES
    engine/src/engine.cpp
    engine/src/voice.cpp
    engine/src/wavetable.cpp
    # engine/src/filter.cpp 
)

pybind11_add_module(ssynth_cpp
    bindings/main_bindings.cpp
    ${ENGINE_SOURCES}
)

target_include_directories(ssynth_cpp PRIVATE 
    engine/include
    ${FFTW3_INCLUDE_DIR}
    ${OPENMP_INCLUDE_DIR}
)

target_link_libraries(ssynth_cpp PRIVATE 
    OpenMP::OpenMP_CXX 
    ${FFTW_LIBRARIES}
)

if(APPLE)
    set_property(TARGET ssynth_cpp PROPERTY INSTALL_RPATH ${INSTALL_RPATH_PATHS})
endif()

if(NOT CMAKE_BUILD_TYPE MATCHES Debug)
    target_compile_options(ssynth_cpp PRIVATE -O3 -ffast-math)
endif()