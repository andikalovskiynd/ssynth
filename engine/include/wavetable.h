#pragma once
#include <vector>
#include <string>
#include <cmath>
#include <iostream>
#include <memory>

// Struct that keeps all the MIPs for singular wave in one continous array
struct FlatWavetable {
    // One big array. If there are 12 MIPs by 2048, size is 24576 floats.
    // float is 4 bytes => general size is ~96 kB
    std::vector<float> data; 
    
    // Idxs where every MIP level starts 
    std::vector<int> mip_offsets; 
    
    int base_size; 
    int num_mips;
};

class WavetableManager {
public:
    WavetableManager(int sample_rate);
    ~WavetableManager();

    int load_table(const std::string& name, const std::string& filepath);
    int get_table_id(const std::string& name) const;

    // Real-Time render
    void render(
        int table_id,
        double& current_phase, 
        double phase_inc,
        int num_frames,
        double amplitude,
        float* output_buffer
    );

private:
    int sample_rate_;
    
    // Vector for all uploaded tables 
    std::vector<FlatWavetable> tables_;
    
    std::vector<std::pair<std::string, int>> registry_;
};