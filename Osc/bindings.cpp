#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "wavetable.h"

namespace py = pybind11;

static WavetableManager* global_manager = nullptr;

PYBIND11_MODULE(wavetable_cpp, m) {
    m.doc() = "Wavetable module";
    
    m.def("init", [](int sample_rate) {
        if (global_manager) delete global_manager;
        global_manager = new WavetableManager(sample_rate);
    }, py::arg("sample_rate") = 44100.0);

    m.def("generate_table", [](const std::string& name, int size) {
        if (!global_manager) global_manager = new WavetableManager(44100.0);
        global_manager->ensure_table(name, size);
    });

    m.def("has_table", [](const std::string& name) {
        if (!global_manager) return false;
        return global_manager->has_table(name);
    });

    m.def("render", []  (const std::string& name,
                        double start_phase,
                        double phase_inc,
                        int num_frames,
                        double amplitude,
                        double phase_offset) 
        {
            if (!global_manager) global_manager = new WavetableManager(44100);

            // ?
            py::gil_scoped_release release;
            auto vec = global_manager->render(name, start_phase, phase_inc, num_frames, amplitude, phase_offset);
            py::gil_scoped_acquire acquire;

            // move to numpy array
            py::array_t<double> arr(num_frames);
            std::memcpy(arr.mutable_data(), vec.data(), sizeof(double) * num_frames);
            return arr;
    },  py::arg("name"), py::arg("start_phase"), py::arg("phase_inc"), py::arg("num_frames"), 
        py::arg("amplitude")=1.0, py::arg("phase_offset")=0.0);
}