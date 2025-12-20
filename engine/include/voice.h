#pragma once
#include "osc.h"
#include "envelope.h"

class Voice {
private:
    Envelope amp_env;

    float env_attack = 0.01f;
    float env_decay = 0.2f;
    float env_sustain = 0.7f;
    float env_release = 0.5f;

    // Convert midi (note) to frequency
    float mtof(int note);

    int sample_rate;
    bool active = false;
    int current_note = -1;
    float velocity = 0.0f;

    float gain = 1.0f;    
    float pan = 0.0f; 
    
    // Oscs
    Oscillator osc1;
    Oscillator osc2;
    Oscillator osc3;

    // Oscs parameters
    int osc1_id = -1;
    int osc2_id = -1;
    int osc3_id = -1;

    float osc1_mix = 1.0f;
    float osc2_mix = 0.0f;
    float osc3_mix = 0.0f;
    
    // Tuning (in semitones)
    float osc1_semi = 0.0f; float osc1_detune = 0.0f;
    float osc2_semi = 0.0f; float osc2_detune = 0.0f;
    float osc3_semi = 0.0f; float osc3_detune = 0.0f;

    // Temporary buffers
    std::vector<float> voice_mix_buffer;    // Mono sum of oscs
    std::vector<float> temp_osc_buffer;     // Temp for other oscs

public:
    Voice(WavetableManager& wm, int _sample_rate);

    bool is_active() const { return active; }
    int get_note() const { return current_note; }

    // Voice management
    void note_on(int note, float velocity);
    void note_off();

    void set_param(int param_id, float value);

    void render(float* left_out, float* right_out, int num_frames);

};