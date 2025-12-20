#pragma once
#include <vector>
#include <atomic>
#include <cmath>
#include <cstring>

class RingBuffer {
public:
    void resize(size_t size) {
        buffer_.resize(size, 0.0f);
        write_pos_ = 0;
    }

    // Called from Audio Thread 
    void write(const float* data, size_t num_frames, int stride = 1) {
        size_t size = buffer_.size();
        size_t wrt = write_pos_.load(std::memory_order_relaxed);
        size_t space_at_end = size - wrt;

        if (num_frames <= space_at_end) {
            // Dont need to wrap
            std::memcpy(&buffer_[wrt], data, num_frames * sizeof(float));
            wrt += num_frames;
        } else {
            // Wrap around
            // Write till the end
            std::memcpy(&buffer_[wrt], data, space_at_end * sizeof(float));
            // Write remainder to the starts
            size_t remaining = num_frames - space_at_end;
            std::memcpy(&buffer_[0], data + space_at_end, remaining * sizeof(float));
            wrt = remaining;
        }
        
        if (wrt >= size) wrt = 0; 
        write_pos_.store(wrt, std::memory_order_release);
    }

    // Called from GUI
    std::vector<float> read_latest(size_t n) {
        std::vector<float> result(n);
        size_t size = buffer_.size();
        size_t w = write_pos_.load(std::memory_order_acquire);
        
        size_t start_idx = (w + size - n) % size;
        size_t space_at_end = size - start_idx;
        
        if (n <= space_at_end) {
            std::memcpy(result.data(), &buffer_[start_idx], n * sizeof(float));
        } else {
            std::memcpy(result.data(), &buffer_[start_idx], space_at_end * sizeof(float));
            std::memcpy(result.data() + space_at_end, &buffer_[0], (n - space_at_end) * sizeof(float));
        }
        return result;
    }


private: 
    std::vector<float> buffer_;
    std::atomic<size_t> write_pos_{0};
};