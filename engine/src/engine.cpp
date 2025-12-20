#include "../include/engine.h"
#include "../include/voice.h"
#include <cmath>

/*
    Initialization
*/ 


SynthEngine::SynthEngine(int _sample_rate) : sample_rate(_sample_rate), wt_manager(_sample_rate) {
    for (int i = 0; i < PARAM_COUNT; ++i) params[i] = 0.0f;

    params[MASTER_VOL] = 0.4f;
    params[FILTER_CUTOFF] = 22050.0f;
    params[AMP_DECAY] = 0.5f;
    params[AMP_SUSTAIN] = 1.0f;

    initVoices();
    initFFT();
    ring_buffer.resize(VISUALIZATION_BUFFER_SIZE);

    buf_l.resize(4096);
    buf_r.resize(4096);
}

SynthEngine::~SynthEngine() {
    if (fft_plan) fftwf_destroy_plan(fft_plan);
    if (fft_in) fftwf_free(fft_in);
    if (fft_out) fftwf_free(fft_out);
}

void SynthEngine::initVoices() {
    voices.reserve(MAX_VOICES);
    for (int i = 0; i < MAX_VOICES; ++i) {
        voices.push_back(std::make_unique<Voice>(wt_manager, sample_rate));
    }
}

void SynthEngine::initFFT() {
    fft_in = (float*)fftwf_malloc(sizeof(float) * FFT_SIZE);
    fft_out = (fftwf_complex*)fftwf_malloc(sizeof(fftw_complex) * (FFT_SIZE / 2 + 1));
    fft_plan = fftwf_plan_dft_r2c_1d(FFT_SIZE, fft_in, fft_out, FFTW_ESTIMATE);
    spectrum_cache.resize(FFT_SIZE / 2 + 1);
}

/*
    Control
*/ 


int SynthEngine::load_wavetable(const std::string& name, const std::string& path) { 
    return wt_manager.load_table(name, path);
}

void SynthEngine::note_on(int note, float velocity) {
    Voice* target_voice = nullptr;

    for (const auto& v : voices) { 
        if (!v->is_active()) {
            target_voice = v.get();
            break;
        }
    }

    // Redo, temporary method
    if (!target_voice) target_voice = voices[0].get();

    target_voice->set_param(AMP_ATTACK, params[AMP_ATTACK]);
    target_voice->set_param(AMP_DECAY, params[AMP_DECAY]);
    target_voice->set_param(AMP_SUSTAIN, params[AMP_SUSTAIN]);
    target_voice->set_param(AMP_RELEASE, params[AMP_RELEASE]);

    // Apply global parameters
    for (int i = 0; i < PARAM_COUNT; ++i) {
        target_voice->set_param(i, params[i]);
    }

    target_voice->note_on(note, velocity);
}

void SynthEngine::note_off(int note) {
    for (const auto& v : voices) {
        if (v->is_active() && v->get_note() == note) {
            v->note_off();
        }
    }
}

void SynthEngine::set_param(int param_id, float value) {
    if (param_id >= 0 && param_id < PARAM_COUNT) {
        params[param_id] = value;

        // Real-time parameters change
        for (const auto& v : voices) {
            if (v->is_active()) v->set_param(param_id, value);
        }
    }
}

float SynthEngine::get_param(int param_id) {
    if (param_id >= 0 && param_id < PARAM_COUNT) return params[param_id];
    return 0.0f;
}

/*
    Processing
*/ 

// Main render method
void SynthEngine::render(float* left_out, float* right_out, int num_frames) {

    // Clear buffers
    std::memset(left_out, 0, num_frames * sizeof(float));
    std::memset(right_out, 0, num_frames * sizeof(float));

    // Summarize voices
    for (const auto& v : voices) {
        if (v->is_active()) v->render(left_out, right_out, num_frames);
    }

    // Master FX and volume
    float master_gain = params[MASTER_VOL];

    // Main loop
    #pragma omp simd
    for (int i = 0; i < num_frames; ++i) {
        left_out[i] *= master_gain;
        right_out[i] *= master_gain;

        // Hard limiter, needed to get rid of clipping due to polyphony
        if (left_out[i] > 1.0f) left_out[i] = 1.0f;
        else if (left_out[i] < -1.0f) left_out[i] = -1.0f;

        if (right_out[i] > 1.0f) right_out[i] = 1.0f;
        else if (right_out[i] < -1.0f) right_out[i] = -1.0f;
    }
}

// Interleaved for python (spectrogram especially)
void SynthEngine::render_interleaved(float* output, int num_frames) {
    // Using static buffers not to allocate memory with every call

    if (num_frames > (int)buf_l.size()) {
        std::cerr << "Buffer overflow in render_interleaved!" << std::endl;
        std::memset(output, 0, num_frames * 2 * sizeof(float));
        return; 
    }

    // Usual render
    render(buf_l.data(), buf_r.data(), num_frames);

    // Interleaving [L, R, L, R...]
    const float* l_ptr = buf_l.data();
    const float* r_ptr = buf_r.data();

    // Write to ring buffer for spectrogram
    ring_buffer.write(l_ptr, num_frames); 

    for (int i = 0; i < num_frames; ++i) {
        output[i * 2 + 0] = l_ptr[i];
        output[i * 2 + 1] = r_ptr[i];
    }
}

/*
    Visualisation
*/ 

std::vector<float> SynthEngine::get_spectrum_data() {
    std::lock_guard<std::mutex> lock(fft_mutex);

    std::vector<float> raw = ring_buffer.read_latest(FFT_SIZE);

    // Apply Hanning window
    for (int i = 0; i < FFT_SIZE; ++i) {
        double window = 0.5 * (1 - std::cos(2.0 * M_PI * i / (FFT_SIZE - 1.0)));
        fft_in[i] = raw[i] * window;
    }

    fftwf_execute(fft_plan);

    // Calculate magnitudes and convert to dB
    int num_bins = FFT_SIZE / 2 + 1;
    float norm_factor = 2.0f / (float)FFT_SIZE;

    for (int i = 0; i < num_bins; ++i) {
        float re = fft_out[i][0];
        float im = fft_out[i][1];

        // Magnitude
        float mag = std::sqrt(re * re + im * im) * norm_factor;

        // dBFS (deciBells relative to Full Scale)
        float db = 20.0f * std::log10(mag + 1e-9f);

        // Mapping: -100dB ... 0 dB --> 0.0 .. 1.0
        float val = (db + 100.0f) / 100.0f;

        // Clamp
        if (val < 0.0f) val = 0.0f;
        if (val > 1.0f) val = 1.0f;

        spectrum_cache[i] = val;
    }

    return spectrum_cache;
}