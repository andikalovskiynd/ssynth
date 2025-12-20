#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "../engine/include/engine.h" 
#include "../engine/include/defs.h"

namespace py = pybind11;

// This function sends numpy array to python
// This is zero-copy way, because we work with numpy/sounddevice directly
void render_to_buffer(SynthEngine& engine, py::array_t<float> output_array) {
    py::buffer_info buf = output_array.request();

    if (buf.ndim != 2) {
        throw std::runtime_error("Output buffer must be 2D (frames x channels)");
    }
    if (buf.shape[1] != 2) {
        throw std::runtime_error("Output buffer must be stereo (2 channels)");
    }

    float* ptr = static_cast<float*>(buf.ptr);
    int num_frames = (int)buf.shape[0];

    engine.render_interleaved(ptr, num_frames);
}

PYBIND11_MODULE(ssynth_cpp, m) {
    m.doc() = "SSynth Core Engine";

    py::enum_<ParamID>(m, "Params")
        // Master
        .value("MASTER_VOL", MASTER_VOL)
        
        // OSC 1
        .value("OSC1_TYPE", OSC1_TYPE)
        .value("OSC1_PITCH", OSC1_PITCH)
        .value("OSC1_DETUNE", OSC1_DETUNE)
        .value("OSC1_MIX", OSC1_MIX)
        
        // OSC 2
        .value("OSC2_TYPE", OSC2_TYPE)
        .value("OSC2_PITCH", OSC2_PITCH)
        .value("OSC2_DETUNE", OSC2_DETUNE)
        .value("OSC2_MIX", OSC2_MIX)

        // OSC 3
        .value("OSC3_TYPE", OSC3_TYPE)
        .value("OSC3_PITCH", OSC3_PITCH)
        .value("OSC3_DETUNE", OSC3_DETUNE)
        .value("OSC3_MIX", OSC3_MIX)

        // Filter
        .value("FILTER_CUTOFF", FILTER_CUTOFF)
        .value("FILTER_RES", FILTER_RES)
        .value("FILTER_TYPE", FILTER_TYPE)
        .value("FILTER_ENV_AMT", FILTER_ENV_AMT)

        // Amp Envelope 
        .value("AMP_ATTACK", AMP_ATTACK)
        .value("AMP_DECAY", AMP_DECAY)
        .value("AMP_SUSTAIN", AMP_SUSTAIN)
        .value("AMP_RELEASE", AMP_RELEASE)

        // Filter Envelope
        .value("FILT_ATTACK", FILT_ATTACK)
        .value("FILT_DECAY", FILT_DECAY)
        .value("FILT_SUSTAIN", FILT_SUSTAIN)
        .value("FILT_RELEASE", FILT_RELEASE)
        
        .export_values();

    // SynthEngine class export
    py::class_<SynthEngine>(m, "Engine")
        .def(py::init<int>(), py::arg("sample_rate") = 44100)
        
        .def("load_wavetable", &SynthEngine::load_wavetable, "Load .wvt file, returns ID")
        
        .def("note_on", &SynthEngine::note_on)
        .def("note_off", &SynthEngine::note_off)
        
        .def("set_param", &SynthEngine::set_param)
        .def("get_param", &SynthEngine::get_param)

        .def("process", &render_to_buffer, "Render audio into provided numpy array")

        .def("get_spectrum", &SynthEngine::get_spectrum_data, "Get FFT magnitudes for visualization");
}