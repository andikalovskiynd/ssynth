#pragma once
#include <algorithm>

class Envelope {
public:
    enum State { IDLE, ATTACK, DECAY, SUSTAIN, RELEASE };

    Envelope(int sample_rate) : sample_rate(sample_rate) {
        reset();
    }

    void reset() {
        state = IDLE;
        current_level = 0.0f;
        release_start_level = 0.0f;
        sustain_counter = 0;
    }

    // sustain_time < 0 means infinite sustain (while the key is pressed)
    void set_params(float attack, float decay, float sustain, float release, float sustain_time = -1.0f) {
        attack = std::max(0.001f, attack);
        decay = std::max(0.001f, decay);
        release = std::max(0.001f, release);
        sustain = std::max(0.0f, std::min(1.0f, sustain));

        // Preprocessing so we can sum instead of fractioning in every sample
        attack_rate = 1.0f / (attack * sample_rate);
        decay_rate = (1.0f - sustain) / (decay * sample_rate);
        release_rate = 1.0f / (release * sample_rate);
        
        use_auto_release = (sustain_time > 0.0f);
        if (use_auto_release) {
            sustain_max_samples = (int)(sustain_time * sample_rate);
        }
    }

    // note_on
    void gate(bool on) {
        if (on) {
            state = ATTACK;
            current_level = 0.0f; // Reset to 0 (hard restart) or keep current if retriggering
            sustain_counter = 0;
        } else {
            // note_off
            if (state != IDLE) {
                state = RELEASE;
                release_start_level = current_level; // Memorize the falling level
            }
        }
    }

    // True if curve still works (simultaneously with voice)
    bool isActive() const {
        return state != IDLE;
    }

    // Main logic for every sample
    float process() {
        switch (state) {
            case IDLE:
                current_level = 0.0f;
                break;

            case ATTACK:
                current_level += attack_rate;
                if (current_level >= 1.0f) {
                    current_level = 1.0f;
                    state = DECAY;
                }
                break;

            case DECAY:
                current_level -= decay_rate;
                if (current_level <= sustain) {
                    current_level = sustain;
                    state = SUSTAIN;
                    sustain_counter = 0;
                }
                break;

            case SUSTAIN:
                current_level = sustain;
                if (use_auto_release) {
                    sustain_counter++;
                    if (sustain_counter >= sustain_max_samples) {
                        gate(false); // Trigger release
                    }
                }
                break;

            case RELEASE:
                // We don't just fall down, but rather proportionally to the starting release level
                // But to make the decay go from the current point to 0 over the Release time
                // We use a fixed release_rate, calculated from 1.0 to 0
                current_level -= release_rate;
                if (current_level <= 0.0f) {
                    current_level = 0.0f;
                    state = IDLE;
                }
                break;
        }
        return current_level;
    }

private:
    int sample_rate;
    State state = IDLE;
    
    float current_level = 0.0f;
    float release_start_level = 0.0f;

    // Parameters
    float sustain = 0.7f;
    
    // Rates (increment for 1 sample)
    float attack_rate = 0.0f;
    float decay_rate = 0.0f;
    float release_rate = 0.0f;

    // Sustain timer
    bool use_auto_release = false;
    int sustain_counter = 0;
    int sustain_max_samples = 0;
};