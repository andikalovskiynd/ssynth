cmake_minimum_required(VERSION 3.15)
project(ssynth CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(APPLE)
    execute_process(COMMAND brew --prefix llvm OUTPUT_VARIABLE LLVM_PREFIX OUTPUT_STRIP_TRAILING_WHITESPACE)
    execute_process(COMMAND brew --prefix libomp OUTPUT_VARIABLE OpenMP_PREFIX OUTPUT_STRIP_TRAILING_WHITESPACE)
    execute_process(COMMAND brew --prefix fftw OUTPUT_VARIABLE FFTW_PREFIX OUTPUT_STRIP_TRAILING_WHITESPACE)

    set(HOMEBREW_CLANG_CXX "${LLVM_PREFIX}/bin/clang++")
    if(EXISTS ${HOMEBREW_CLANG_CXX})
        set(CMAKE_CXX_COMPILER ${HOMEBREW_CLANG_CXX} CACHE FILEPATH "Homebrew Clang C++ Compiler" FORCE)
    else()
        message(FATAL_ERROR "Homebrew Clang not found at ${HOMEBREW_CLANG_CXX}. Ensure 'brew install llvm' is complete.")
    endif()

    set(OPENMP_DIR "${OpenMP_PREFIX}/lib")
    set(FFTW_DIR "${FFTW_PREFIX}/lib")

    set(OPENMP_COMPILE_OPTIONS "-fopenmp") 
    set(OPENMP_LINK_FLAGS "-lomp")
    set(FFTW_LINK_FLAGS "-lfftw3")
    
    include_directories(${OpenMP_PREFIX}/include) 
    
    set(CMAKE_MACOSX_RPATH 1)
    
    set(INSTALL_RPATH_PATHS "${OPENMP_DIR};${FFTW_DIR};@rpath")
endif()

find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG REQUIRED)
find_package(FFTW3 REQUIRED) 

pybind11_add_module(wavetable_cpp
    Osc/bindings.cpp
    Osc/wavetable.cpp
)

if(APPLE)
    target_compile_options(wavetable_cpp PRIVATE ${OPENMP_COMPILE_OPTIONS})
    
    target_link_directories(wavetable_cpp PRIVATE ${OPENMP_DIR})
    
    set_property(TARGET wavetable_cpp PROPERTY INSTALL_RPATH ${INSTALL_RPATH_PATHS})
    
    target_link_libraries(wavetable_cpp PRIVATE ${OPENMP_LINK_FLAGS})
endif()

target_include_directories(wavetable_cpp PRIVATE Osc)

pybind11_add_module(spectrogram_cpp
    gui/visual/spectrogram/bindings_spectrogram.cpp
    gui/visual/spectrogram/fftw_setup.cpp
    gui/visual/spectrogram/spectrogram_vis.cpp
)

if(APPLE)
    target_compile_options(spectrogram_cpp PRIVATE ${OPENMP_COMPILE_OPTIONS})
    
    target_link_directories(spectrogram_cpp PRIVATE ${FFTW_DIR} ${OPENMP_DIR})
    
    set_property(TARGET spectrogram_cpp PROPERTY INSTALL_RPATH ${INSTALL_RPATH_PATHS})
    
    target_link_libraries(spectrogram_cpp PRIVATE 
        Python::Module 
        ${FFTW_LINK_FLAGS}
        ${OPENMP_LINK_FLAGS}
    )
endif()

target_include_directories(spectrogram_cpp PRIVATE gui/visual/spectrogram)

add_library(filter_raw SHARED
    Filter/Raw/low_and_high_filter.cpp
)

set_target_properties(filter_raw PROPERTIES
    PREFIX ""
    OUTPUT_NAME "filter_raw"
)

target_include_directories(filter_raw PRIVATE Filter/Raw)