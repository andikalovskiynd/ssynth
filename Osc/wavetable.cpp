#include "wavetable.h"
#include <fstream>
#include <iostream>
#include <algorithm>
#include <vector>

WavetableManager::WavetableManager(int sample_rate) : sample_rate_(sample_rate) {}
WavetableManager::~WavetableManager() {}

inline double WavetableManager::lookup_linear(const std::vector<double>& table, double phase) {
    const int N = (int)table.size();
    if (N == 0) return 0.0;
    
    double pos = phase * N;
    int i0 = (int)pos;
    double frac = pos - i0;
    
    int i1 = i0 + 1;
    if (i1 >= N) i1 = 0; 

    return table[i0] + frac * (table[i1] - table[i0]);
}

bool WavetableManager::load_wvt(const std::string& name, const std::string& filepath) {
    std::lock_guard<std::mutex> lock(mutex_);

    std::ifstream file(filepath, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "WavetableManager: Failed to open file " << filepath << std::endl;
        return false;
    }

    // 1. Read header
    char magic[4];
    file.read(magic, 4);
    if (std::strncmp(magic, "WVT1", 4) != 0) {
        std::cerr << "WavetableManager: Invalid magic bytes in " << filepath << std::endl;
        return false;
    }

    int32_t num_mips = 0;
    int32_t table_size = 0;
    file.read(reinterpret_cast<char*>(&num_mips), sizeof(int32_t));
    file.read(reinterpret_cast<char*>(&table_size), sizeof(int32_t));

    if (num_mips <= 0 || table_size <= 0) {
        std::cerr << "WavetableManager: Invalid header data (mips=" << num_mips << ", size=" << table_size << ")" << std::endl;
        return false;
    }

    // 2. Prepare structure
    WavetableSet wt;
    wt.numMips = num_mips;
    wt.baseSize = table_size;
    wt.mips.resize(num_mips);

    // 3. Read data
    std::vector<float> temp_buffer(table_size);

    for (int i = 0; i < num_mips; ++i) {
        wt.mips[i].resize(table_size);
        
        file.read(reinterpret_cast<char*>(temp_buffer.data()), table_size * sizeof(float));
        if (!file) {
            std::cerr << "WavetableManager: Unexpected EOF in " << filepath << std::endl;
            return false;
        }

        // Convert float -> double
        for (int j = 0; j < table_size; ++j) {
            wt.mips[i][j] = static_cast<double>(temp_buffer[j]);
        }
    }

    tables_[name] = std::move(wt);
    std::cout << "WavetableManager: Loaded '" << name << "' from " << filepath << std::endl;
    return true;
}

bool WavetableManager::has_table(const std::string& name) {
    std::lock_guard<std::mutex> lock(mutex_);
    return tables_.count(name) > 0;
}

inline double interpolate(double y0, double y1, double frac) {
    return y0 + frac * (y1 - y0);
}

void WavetableManager::render(
    const std::string& name,
    double& current_phase, 
    double phase_inc,
    int num_frames,
    double amplitude,
    std::vector<double>& output_buffer
) {
    WavetableSet* wt = nullptr;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = tables_.find(name);
        if (it != tables_.end()) {
            wt = &it->second;
        }
    }

    if (!wt || wt->mips.empty()) {
        std::fill(output_buffer.begin(), output_buffer.begin() + num_frames, 0.0);
        return;
    }

    // MipMapping (Interpolation between MIP-levels)
    // step = how much samples we process by one cycle
    double step = phase_inc * wt->baseSize;
    
    // Calculate floating table idx 
    // log2(step) gives neccesery octave
    // Ex: step=1 -> idx=0. step=2 -> idx=1. step=4 -> idx=2.
    double table_idx_float = 0.0;
    if (step >= 1.0) {
        table_idx_float = std::log2(step);
    }
    
    if (table_idx_float < 0.0) table_idx_float = 0.0;
    // -1.001 so there is always a "next" value to look up, except the edge
    if (table_idx_float > wt->numMips - 1.001) table_idx_float = wt->numMips - 1.001;

    int idx0 = (int)table_idx_float;
    int idx1 = idx0 + 1;
    if (idx1 >= wt->numMips) idx1 = wt->numMips - 1;

    // Coefficient of mixing (for smoothness of note transitions)
    double mix_mips = table_idx_float - idx0;

    const std::vector<double>& table0 = wt->mips[idx0];
    const std::vector<double>& table1 = wt->mips[idx1];

    // Debug because there are currently some problems with rendering
    static bool data_checked = false;
    if (!data_checked && name == "saw") {
        std::cout << "--- CHECKING SAW TABLE DATA (MIP " << idx0 << ") ---" << std::endl;
        for (int k = 0; k < 10; ++k) {
            std::cout << "[" << k << "] = " << table0[k] << std::endl;
        }
        std::cout << "---------------------------------------------" << std::endl;
        data_checked = true;
    }

    for (int i = 0; i < num_frames; ++i) {
        // Read MIP from N-th level
        double val0 = lookup_linear(table0, current_phase);
        
        // Read MIP from N-th + 1 level
        double val1 = lookup_linear(table1, current_phase);
        
        // Trilinear lookup 
        double final_val = interpolate(val0, val1, mix_mips);

        output_buffer[i] = amplitude * final_val;
        
        // Update phase
        current_phase += phase_inc;
        
        // Wrap
        if (current_phase >= 1.0) {
            current_phase -= std::floor(current_phase);
        }
    }
}