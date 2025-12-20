#pragma once
#include <vector>
#include <memory>
#include <string> 
#include <mutex>
#include <fftw3.h>

#include "defs.h"
#include "voice.h"
#include "utils.h"
#include "wavetable.h"

class SynthEngine {
private: 
    int sample_rate;
    WavetableManager wt_manager;
    std::vector<std::unique_ptr<Voice>> voices;

    float params[PARAM_COUNT];
    RingBuffer ring_buffer;

    float* fft_in;
    fftwf_complex* fft_out;
    fftwf_plan fft_plan;
    std::vector<float> spectrum_cache;      // Return to python
    std::mutex fft_mutex;

    // Helpers
    void initFFT();
    void initVoices();

    std::vector<float> buf_l;
    std::vector<float> buf_r;

public:
    SynthEngine(int sample_rate);
    ~SynthEngine();

    // Control API 

    // Loading of resources
    int load_wavetable(const std::string& name, const std::string& path);

    // Notes control (MIDI in future?)
    void note_on(int note_number, float velocity);
    void note_off(int note_number);

    // Parameters
    void set_param(int param_id, float value);
    float get_param(int param_id);

    // Heart 
    void render(float* left, float* right, int num_frames);
    void render_interleaved(float* interleaved, int num_frames);    // for python
    std::vector<float> get_spectrum_data();
};