#include "spectrogram_vis.h"
#include <cmath>

void apply_hanning_window(std::vector<double>& buffer) {
    int N = (int)buffer.size();
    if (N == 0) return;

    // Parallelization is possible due to independency of every sample piece 
    #pragma omp parallel for
    for (int i = 0; i < N; ++i) {
        double window_val = 0.5 * (1 - std::cos(2.0 * M_PI * i / (N - 1.0)));
        buffer[i] *= window_val;
    }
}

std::vector<double> calculate_spectrum_fftw(const std::vector<double>& buffer) {
    int N = (int)buffer.size();
    if (N == 0 || (N & (N - 1)) != 0) return {};

    static double* in = nullptr;
    static fftw_complex* out = nullptr;
    static fftw_plan plan = nullptr;
    static int prev_N = 0;

    // Init a plan
    if (N != prev_N) {
        if (plan) { fftw_destroy_plan(plan); fftw_free(in); fftw_free(out); }
        in = (double*)fftw_malloc(sizeof(double) * N);
        out = (fftw_complex*)fftw_malloc(sizeof(fftw_complex) * (N / 2 + 1));
        plan = fftw_plan_dft_r2c_1d(N, in, out, FFTW_ESTIMATE);
        prev_N = N;
    }

    std::vector<double> windowed = buffer;
    apply_hanning_window(windowed);
    std::copy(windowed.begin(), windowed.end(), in);

    fftw_execute(plan);

    int num_bins = N / 2 + 1;
    std::vector<double> magnitudes(num_bins);
    
    double normalization = 2.0 / N; 
    
    #pragma omp parallel for
    for (int i = 0; i < num_bins; ++i) {
        double re = out[i][0];
        double im = out[i][1];
        magnitudes[i] = std::sqrt(re*re + im*im) * normalization;
    }
    
    return magnitudes;
}