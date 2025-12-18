#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "wavetable.h"

namespace py = pybind11;
static WavetableManager* global_manager = nullptr;

PYBIND11_MODULE(wavetable_cpp, m) {
    m.doc() = "Wavetable module with Anti-Aliasing support";

    m.def("init", [](int sample_rate) {
        if (global_manager) delete global_manager;
        global_manager = new WavetableManager(sample_rate);
    }, py::arg("sample_rate") = 44100);

    m.def("load_wvt", [](const std::string& name, const std::string& filepath) {
        if (!global_manager) global_manager = new WavetableManager(44100);
        return global_manager->load_wvt(name, filepath);
    }, py::arg("name"), py::arg("filepath"));

    m.def("has_table", [](const std::string& name) {
        if (!global_manager) return false;
        return global_manager->has_table(name);
    }, py::arg("name"));

    m.def("render", [](const std::string& name,
                       double start_phase,
                       double phase_inc,
                       int num_frames,
                       double amplitude) 
    {
        if (!global_manager) global_manager = new WavetableManager(44100);

        std::vector<double> buffer(num_frames);
        
        double current_phase = start_phase;

        {
            py::gil_scoped_release release;
            global_manager->render(name, current_phase, phase_inc, num_frames, amplitude, buffer);
        }

        py::array_t<double> result(num_frames);
        std::memcpy(result.mutable_data(), buffer.data(), sizeof(double) * num_frames);

        return py::make_tuple(result, current_phase);

    }, py::arg("name"), 
       py::arg("start_phase"), 
       py::arg("phase_inc"), 
       py::arg("num_frames"), 
       py::arg("amplitude") = 1.0);
    
    m.add_object("_cleanup", py::capsule([]() {
        if (global_manager) {
            delete global_manager;
            global_manager = nullptr;
        }
    }));
}