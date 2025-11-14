#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <cmath>
#include <cstring>

#include "fftw_setup.h"
#include "spectrogram_vis.h"

namespace py = pybind11;

std::vector<double> calculate_spectrum_fftw(const std::vector<double>& audio_buffer);

PYBIND11_MODULE(spectrogram_cpp, m) {
    m.doc() = "Spectrogram module";
    m.def("init_fftw", []() {
        if (!init_fftw()) throw std::runtime_error("Failed to init FFTW threads");
    }, "Init FFTW for multithreading");

    m.def("cleanup_fft", &cleanup_fftw, "Cleans up FFTW threads upon exit");

    m.def("calculate_spectrum_fftw", [](py::array_t<double, py::array::c_style> arr) {
        std::vector<double> vec(arr.data(), arr.data() + arr.size());

        py::gil_scoped_release release;
        std::vector<double> spectrum = calculate_spectrum_fftw(vec);
        py::gil_scoped_acquire acquire;

        py::array_t<double> out(spectrum.size());
        std::memcpy(out.mutable_data(), spectrum.data(), sizeof(double) * spectrum.size());

        return out;
    }, py::arg("buffer"), "Calculates spectrum magnitudes");
}