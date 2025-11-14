#include <fftw3.h>
#include <omp.h>
#include <iostream>

// Initialize the FFTW only once for multi thread work
bool init_fftw();

// Cleanup
void cleanup_fftw();