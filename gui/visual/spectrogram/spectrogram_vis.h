#include <fftw3.h>
#include <cmath>
#include <omp.h>
#include <vector>

/**
 * There is no any chance to use real FFT transformation in real-time spectral analysis
 * so for making it possible we must use a short-time Fourrier transform (оконное преобразование Фурье)
 * according to this fancy formula:
 * STFT{x(t)}{tau, omega} = int from -inf to +inf (x(t) * w(t - tau) * exp(-i * omega * t) dt)
 * Where w(tau) is the window function (we are using Hanning for this project)
 * And x(t) is the transforming signal itself 
 * 
 * `Hanning window`: w(n) = 0.5 * (1 - cos (2pi*n / N - 1 )), where N is width of the window
*/
void apply_hanning_window(std::vector<double>& buffer);

std::vector<double> calculate_magnitude(fftw_complex* fft_output, int N);

std::vector<double> calculate_spectrum_fftw(const std::vector<double>& buffer);