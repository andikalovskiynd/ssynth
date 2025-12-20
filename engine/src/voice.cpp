#include "../include/voice.h"
#include "../include/defs.h"
#include <algorithm>
#include <cstring>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

Voice::Voice(WavetableManager& wm, int _sample_rate) : 
    sample_rate(_sample_rate), 
    osc1(wm, sample_rate), 
    osc2(wm, sample_rate), 
    osc3(wm, sample_rate), 
    amp_env(_sample_rate) 
    {
        // Reserve for maximum size of block
        voice_mix_buffer.resize(2048);
        temp_osc_buffer.resize(2048);
        amp_env.set_params(env_attack, env_decay, env_sustain, env_release);
} 

float Voice::mtof(int note) {
    return 440.0f * std::pow(2.0f, (note - 69.0f) / 12.0f);
}

void Voice::note_on(int note, float _velocity) {
    current_note = note;
    velocity = _velocity;
    active = true;

    osc1.reset();
    osc2.reset();
    osc3.reset();

    osc1.set_type(osc1_id);
    osc2.set_type(osc2_id);
    osc3.set_type(osc3_id);

    amp_env.gate(true);
}

void Voice::note_off() {
    amp_env.gate(false);
}

void Voice::set_param(int param_id, float value) {
    bool update_env = false;
    switch(param_id) {

        // Osc1:
        case OSC1_TYPE:     osc1_id = (int)value; break;
        case OSC1_MIX:      osc1_mix = value; break;
        case OSC1_PITCH:    osc1_semi = value; break;
        case OSC1_DETUNE:   osc1_detune = value; break;

        // Osc1:
        case OSC2_TYPE:     osc2_id = (int)value; break;
        case OSC2_MIX:      osc2_mix = value; break;
        case OSC2_PITCH:    osc2_semi = value; break;
        case OSC2_DETUNE:   osc2_detune = value; break;

        // Osc1:
        case OSC3_TYPE:     osc3_id = (int)value; break;
        case OSC3_MIX:      osc3_mix = value; break;
        case OSC3_PITCH:    osc3_semi = value; break;
        case OSC3_DETUNE:   osc3_detune = value; break;

        // ADSR:
        case AMP_ATTACK:  
            env_attack = value; 
            update_env = true; 
            break;
        case AMP_DECAY:   
            env_decay = value; 
            update_env = true; 
            break;
        case AMP_SUSTAIN: 
            env_sustain = value; 
            update_env = true; 
            break;
        case AMP_RELEASE: 
            env_release = value; 
            update_env = true; 
            break;

        default: break;
    }

    if (update_env) {
        amp_env.set_params(env_attack, env_decay, env_sustain, env_release, -1.0f);
    }
}

void Voice::render(float* left_out, float* right_out, int num_frames) {
    if (!amp_env.isActive()) {
        active = false;
        return;
    }

    if ((int)voice_mix_buffer.size() < num_frames) {
        voice_mix_buffer.resize(num_frames);
        temp_osc_buffer.resize(num_frames);
    }

    // Clear main mix of the voice
    std::memset(voice_mix_buffer.data(), 0, num_frames * sizeof(float));

    // Count freqs
    float base_freq = mtof(current_note);

    float fr1 = base_freq * std::pow(2.0f, (osc1_semi + osc1_detune) / 12.0f);
    float fr2 = base_freq * std::pow(2.0f, (osc2_semi + osc2_detune) / 12.0f);
    float fr3 = base_freq * std::pow(2.0f, (osc3_semi + osc3_detune) / 12.0f);

    // Scaling to reduce clipping
    float scale = velocity * gain * 0.33f;

    // Osc1 processing (directly to mix buffer):
    if (osc1_mix >= 0.001f && osc1_id >= 0) {
        osc1.process_adding(voice_mix_buffer.data(), num_frames, fr1, sample_rate, osc1_mix * scale);
    }

    // Osc2 to temp buffer
    if (osc2_mix >= 0.001f && osc2_id >= 0) {
        osc2.process_adding(temp_osc_buffer.data(), num_frames, fr2, sample_rate, osc2_mix * scale);

        // Temp -> Mix
        for (int i = 0; i < num_frames; ++i) {
            voice_mix_buffer[i] += temp_osc_buffer[i];
        }
    }

    // Osc3, use temp buffer again because Osc2 is already in mix and not needed in temp anymore
    if (osc3_mix >= 0.001f && osc3_id >= 0) {
        osc3.process_adding(temp_osc_buffer.data(), num_frames, fr3, sample_rate, osc3_mix * scale);

        for (int i = 0; i < num_frames; ++i) {
            voice_mix_buffer[i] += temp_osc_buffer[i];
        }
    }

    // filter.process

    // Curve applying
    for (int i = 0; i < num_frames; ++i) {
        float env_val = amp_env.process();      // get the value from [0,1]
        voice_mix_buffer[i] *= env_val;
    }

    // Stereo pan and output
    float pan_clamped = std::max(-1.0f, std::min(1.0f, pan));

    // Using Equal-Power method (cos / sin based) instead of linear
    // For example, linear gives 0.5² + 0.5² = 0.5 gain at center, it is too silent
    // Equal-power gives a 0.707² + 0.707² = 1 at center so it is much more realistic
    float angle = (pan_clamped + 1.0f) * (M_PI / 4.0f);
    float l_gain = std::cos(angle);
    float r_gain = std::sin(angle);

    for (int i = 0; i < num_frames; ++i) {
        float mono_sample = voice_mix_buffer[i];

        // Accumulate to global bus 
        left_out[i] += mono_sample * l_gain;
        right_out[i] += mono_sample * r_gain;

    }
}