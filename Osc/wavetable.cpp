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

    // Choose MIP-level (Anti-Aliasing)
    int table_idx = 0;
    if (phase_inc > 0.0) {
        double step = phase_inc * wt->baseSize;
        if (step >= 1.0) {
            table_idx = (int)(std::log2(step)); 
        }
    }

    if (table_idx < 0) table_idx = 0;
    if (table_idx >= wt->numMips) table_idx = wt->numMips - 1;

    const std::vector<double>& selected_table = wt->mips[table_idx];

    // Render itself
    // TODO: Crossfading (interpolation between different tables)
    
    for (int i = 0; i < num_frames; ++i) {
        output_buffer[i] = amplitude * lookup_linear(selected_table, current_phase);
        
        current_phase += phase_inc;
        
        if (current_phase >= 1.0) current_phase -= 1.0;
        else if (current_phase < 0.0) current_phase += 1.0;
    }
}