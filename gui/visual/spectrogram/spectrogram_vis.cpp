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

std::vector<double> calculate_magnitude(fftw_complex* fft_output, int N) {
    int num_bins = N / 2 + 1;
    std::vector<double> magnitudes(num_bins);

    #pragma omp parallel for
    for (int i = 0; i < num_bins; ++i) {
        double re = fft_output[i][0];
        double im = fft_output[i][1];

        // As Magnitude is sqrt(re^2 + im^2)
        magnitudes[i] = std::sqrt(re * re + im * im);
    }
    return magnitudes;
}

std::vector<double> calculate_spectrum_fftw(const std::vector<double>& buffer) {
    int N = (int)buffer.size();

    // It is supposed that N is a power of two
    if (N == 0 || (N & (N - 1)) != 0) {
        return {};
    }

    // Prepare buffer
    // FFTW requires premilinairy allocation of memory due to optimization
    double* in = (double*)fftw_malloc(sizeof(double) * N);
    fftw_complex* out = (fftw_complex*)fftw_malloc(sizeof(fftw_complex) * (N / 2 + 1));     // As we are using the R2C transform (real to complex)
    std::vector<double> windowed_buffer = buffer;

    // Applying the window
    apply_hanning_window(windowed_buffer);
    std::copy(windowed_buffer.begin(), windowed_buffer.end(), in);

    // Make and execute FFTW plan
    fftw_plan plan = fftw_plan_dft_r2c_1d(
        N,              // size
        in,             // input
        out,            // output
        FFTW_ESTIMATE   // flag for plan
    );

    fftw_execute(plan);

    // Magnitude calculation
    std::vector<double> magnitudes = calculate_magnitude(out, N);

    // Clean-up
    fftw_destroy_plan(plan);
    fftw_free(in);
    fftw_free(out);

    return magnitudes;
}