#include "../include/wavetable.h"
#include <fstream>
#include <iostream>
#include <algorithm>
#include <vector>
#include <cstring>

WavetableManager::WavetableManager(int sample_rate) : sample_rate_(sample_rate) {
    tables_.reserve(16);
}
WavetableManager::~WavetableManager() {}

int WavetableManager::get_table_id(const std::string& name) const {
    for (const auto& pair : registry_) {
        if (pair.first == name) return pair.second;
    }
    return -1;
}

int WavetableManager::load_table(const std::string& name, const std::string& filepath) {
    int existing = get_table_id(name);
    if (existing >= 0) return existing;

    std::ifstream file(filepath, std::ios::binary);
    if (!file.is_open()) return -1;

    char magic[4];
    file.read(magic, 4);

    int32_t num_mips, table_size;
    file.read((char*)& num_mips, 4);
    file.read((char*)&table_size, 4);

    // Allocate flat memory
    FlatWavetable wt;
    wt.num_mips = num_mips;
    wt.base_size = table_size;
    wt.mip_offsets.resize(num_mips);

    // Get general size
    size_t general = num_mips * table_size;
    wt.data.resize(general);

    file.read(reinterpret_cast<char*>(wt.data.data()), general * sizeof(float));

    // Fill the MIP offsets
    for (int i = 0; i < num_mips; ++i) {
        wt.mip_offsets[i] = i * table_size;
    } 

    // Save
    int new_id = (int)tables_.size();
    tables_.push_back(std::move(wt));
    registry_.push_back({name, new_id});

    return new_id;
}

static inline float interpolate_linear(float y0, float y1, float frac) {
    return y0 + frac * (y1 - y0);
}

void WavetableManager::render(
    int table_id,
    double& current_phase,
    double phase_inc,
    int num_frames,
    double amplitude,
    float* output_buffer
) {
    if (table_id < 0 || table_id >= tables_.size()) {
        return;
    }

    // Get a link to the struct
    const FlatWavetable& wt = tables_[table_id];
    const float* raw_data = wt.data.data();

    // MIP level calculation
    double step = phase_inc * wt.base_size;
    double table_idx_float = 0.0;

    if (step >= 1.0) table_idx_float = std::log2(step + 0.5);
    if (table_idx_float <= 0) table_idx_float = 0.0;
    else if (table_idx_float > wt.num_mips - 1.001) table_idx_float = wt.num_mips - 1.001;

    int idx0 = (int)table_idx_float;
    int idx1 = idx0 + 1;
    if (idx1 >= wt.num_mips) idx1 = wt.num_mips - 1;
    float mix = (float)(table_idx_float - idx0);

    // Get pointers to beginning of needed tables
    // Instead of wt.mips[idx][sample] we use raw_data[offset + sample]
    // Which is highly optimized
    const float* t0 = raw_data + wt.mip_offsets[idx0];
    const float* t1 = raw_data + wt.mip_offsets[idx1];

    // -- Main logic
    // This has to be the most efficient part
    double pos = current_phase * wt.base_size;
    double inc_in_samples = phase_inc * wt.base_size;
    int mask = wt.base_size - 1;

    float amp_f = (float)amplitude;

    for (int i = 0;  i < num_frames; ++i) {
        int int_pos = (int)pos;
        float frac_pos = (float)(pos - int_pos);

        // Bitwise & mask works only if size is a power of 2 (as it is)
        // Faster than `if (idx >= size) idx = 0;`
        int i_next = (int_pos + 1) & mask;
        int_pos = int_pos & mask;

        // Read from cache
        float val0 = interpolate_linear(t0[int_pos], t0[i_next], frac_pos);
        float val1 = interpolate_linear(t1[int_pos], t1[i_next], frac_pos);

        // Mix MIP levels
        float final_val = val0 + mix * (val1 - val0);

        output_buffer[i] = amp_f * final_val;

        pos += inc_in_samples;
        if (pos >= wt.base_size) pos -= wt.base_size;
    }

    current_phase = pos / wt.base_size;
}