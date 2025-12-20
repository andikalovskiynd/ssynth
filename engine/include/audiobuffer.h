#pragma once
#include <vector>
#include <cstring>
#include <algorithm>

class AudioBuffer {
private:
    int num_frames = 0;
    std::vector<float> left;
    std::vector<float> right;

public:
    AudioBuffer() = default;

    void resize(int _num_frames) {
        if (num_frames != _num_frames) {
            num_frames = _num_frames;
            left.resize(num_frames);
            right.resize(num_frames);
        }
    }

    void clear() {
        std::memset(left.data(), 0, num_frames * sizeof(float));
        std::memset(right.data(), 0, num_frames * sizeof(float));
    }

    // Get raw pointers (DSP-used only)
    float* get_left() { return left.data(); }
    float* get_right() { return right.data(); }
    const float* get_left() const { return left.data(); }
    const float* get_right() const { return right.data(); } 

    int get_size() const { return num_frames; } 

    // Mixing other buffers into this (accumulation)
    void add_from(const AudioBuffer& other) {
        int n = std::min(num_frames, other.num_frames);
        const float* l_src = other.get_left();
        const float* r_src = other.get_right();

        #pragma omp simd
        for (int i = 0; i < num_frames; ++i) {
            left[i] += l_src[i];
            right[i] += r_src[i];
        }
    }

    // Export to interleaved [L,R,L,R...]
    // dest must be size of num_frames * 2 
    void write_interleaved(float* dest) const {
        for (int i = 0; i < num_frames; ++i) {
            dest[i * 2 + 0] = left[i];
            dest[i * 2 + 1] = right[i];
        }
    }
};