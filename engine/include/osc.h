#pragma once
#include "wavetable.h"

class Oscillator {
private:
    WavetableManager& wt_manager;
    int sample_rate;
    double phase = 0.0;
    int table_id = -1;

public:
    Oscillator(WavetableManager& _wt_manager, int _sample_rate) : wt_manager(_wt_manager), sample_rate(_sample_rate) {}

    void set_type(int _table_id) {
        table_id = _table_id;
    }

    void reset() {
        phase = 0.0;
    }

    // Add one oscillator to buffer
    void process_adding(float* output, int num_frames, float freq, int sample_rate, float mix_level) {
        if (table_id < 0 || mix_level < 0.001f) return;

        double phase_inc = (double)freq / (double)sample_rate;

        // WavetableManager::render does `=`, not `+=`
        // so in case of summing the signals, we need 
        // a temp buffer in 'Voice'
        wt_manager.render(table_id, phase, phase_inc, num_frames, (double)mix_level, output);
    }
};