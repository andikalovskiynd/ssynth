#include "fftw_setup.h"

bool init_fftw() {
    int max_threads = omp_get_max_threads();
    // int safe_threads = std::max(2, std::min(4, max_threads / 2));
    int safe_threads = 2;

    if (fftw_init_threads() == 0) {
        std::cerr << "DEBUG: ERROR IN INITIALIZING FFTW MULTITHREADING\n";
        return false;
    }

    fftw_plan_with_nthreads(safe_threads);
    std::cout << "DEBUG: FFTW Initialized with " << safe_threads << " threads (Max available: " << max_threads << ")\n";
    return true;
}

void cleanup_fftw() {
    fftw_cleanup_threads();
}