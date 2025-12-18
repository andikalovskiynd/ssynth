#include "fftw_setup.h"
#include <fftw3.h>

bool init_fftw() {
    int max_threads = omp_get_max_threads();
    // int safe_threads = std::max(2, std::min(4, max_threads / 2));
    if (max_threads <= 0) max_threads = 1;

    if (fftw_init_threads() == 0) {
        std::cerr << "DEBUG: ERROR IN INITIALIZING FFTW MULTITHREADING\n";
        return false;
    }

    fftw_plan_with_nthreads(max_threads);
    std::cout << "DEBUG: FFTW Initialized with " << max_threads << " threads (Max available: " << max_threads << ")\n";

    std::cout << "              DEBUG: Returning true! \n";
    return true;
}

void cleanup_fftw() {
    fftw_cleanup_threads();
}