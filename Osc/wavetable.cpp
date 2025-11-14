#include "wavetable.h"
#include <algorithm>
#include <cmath>
#include <omp.h>

WavetableManager::WavetableManager(int sample_rate) : sample_rate_(sample_rate) {}

WavetableManager::~WavetableManager() {}

inline double WavetableManager::lookup_linear(const std::vector<double>& table, double phase) {
    const int N = (int)table.size();
    if (N == 0) return 0.0;

    // Ensure phase is in [0,1)
    phase = phase - std::floor(phase);

    double pos = phase * (double)N;           // position in [0, N)
    double idx0_d = std::floor(pos);          // integer part
    int i0 = (int)idx0_d % N;
    if (i0 < 0) i0 += N;
    int i1 = i0 + 1;
    if (i1 >= N) i1 = 0;

    double frac = pos - idx0_d;               // fractional part in [0,1)
    return table[i0] * (1.0 - frac) + table[i1] * frac;
}

void WavetableManager::build_bandlimited_saw(std::vector<double>& table, int table_size) {
    table.assign(table_size, 0.0);

    double base_freq = (double)sample_rate_ / table_size;
    int max_harm = std::max(1, (int)std::floor((sample_rate_ / 2.0) / base_freq));

    // #pragma omp parallel for
    for (int i = 0; i < table_size; ++i) {
        double ph = (double)i / table_size;  // position 0..1
        double sum = 0.0;

        // Sum harmonics up to Nyquist
        for (int j = 1; j <= max_harm; ++j) {
            sum += (1.0 / j) * std::sin(2.0 * M_PI * j * ph);
        }

        table[i] = sum;
    }

    // Normalize 
    double peak = 0.0;
    for (double s : table) peak = std::max(peak, std::abs(s));
    if (peak > 0.0) {
        // #pragma omp parallel for
        for (int i = 0; i < table_size; ++i) table[i] /= peak;
    }
}

void WavetableManager::build_bandlimited_square(std::vector<double>& table, int table_size) {
    table.assign(table_size, 0.0);

    double base_freq = (double)sample_rate_ / table_size;
    int max_harm = std::max(1, (int)std::floor((sample_rate_ / 2.0) / base_freq));

    // #pragma omp parallel for
    for (int i = 0; i < table_size; ++i) {
        double ph = (double)i / table_size;
        double sum = 0.0;

        for (int j = 1; j <= max_harm; j += 2) {
            sum += (1.0 / j) * std::sin(2.0 * M_PI * j * ph);   // odd harmonics
        }

        table[i] = sum;
    }

    // Normalize 
    double peak = 0.0;
    for (double s : table) peak = std::max(peak, std::abs(s));
    if (peak > 0.0) {
        // #pragma omp parallel for
        for (int i = 0; i < table_size; ++i) table[i] /= peak;
    }
}

void WavetableManager::build_bandlimited_triangle(std::vector<double>& table, int table_size) {
    table.assign(table_size, 0.0);

    double base_freq = (double)sample_rate_ / table_size;
    int max_harm = std::max(1, (int)std::floor((sample_rate_ / 2.0) / base_freq));

    // #pragma omp parallel for
    for (int i = 0; i < table_size; ++i) {
        double ph = (double)i / table_size;
        double sum = 0.0;
        int sign = 1;

        for (int j = 1; j <= max_harm; j += 2) {
            sum += sign * (1.0 / (j * j)) * std::sin(2.0 * M_PI * j * ph);    // For triangle sum odd harmonics with (1/k^2) and alternating sign
            sign *= -1;
        }

        table[i] = sum;
    }

    // Normalize 
    double peak = 0.0;
    for (double s : table) peak = std::max(peak, std::abs(s));
    if (peak > 0.0) {
        // #pragma omp parallel for
        for (int i = 0; i < table_size; ++i) table[i] /= peak;
    }
}

void WavetableManager::build_sine(std::vector<double>& table, int table_size) {
    table.resize(table_size);
    // #pragma omp parallel for
    for (int i = 0; i < table_size; ++i) {
        double ph = (double)i / table_size;
        table[i] = std::sin(2.0 * M_PI * ph);
    }
}

// ============================================================================== //

void WavetableManager::generate_sine(const std::string& name, int table_size) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<double> tbl;
    build_sine(tbl, table_size);
    tables_[name] = std::move(tbl);
}

void WavetableManager::generate_saw(const std::string& name, int table_size) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<double> tbl;
    build_bandlimited_saw(tbl, table_size);
    tables_[name] = std::move(tbl);
}

void WavetableManager::generate_square(const std::string& name, int table_size) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<double> tbl;
    build_bandlimited_square(tbl, table_size);
    tables_[name] = std::move(tbl);
}

void WavetableManager::generate_triangle(const std::string& name, int table_size) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<double> tbl;
    build_bandlimited_triangle(tbl, table_size);
    tables_[name] = std::move(tbl);
}

void WavetableManager::ensure_table(const std::string& name, int table_size) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (tables_.count(name)) {
        if ((int)tables_[name].size() == table_size) return;
    }

    if (name == "sine") build_sine(tables_[name], table_size);
    else if (name == "saw") build_bandlimited_saw(tables_[name], table_size);
    else if (name == "square") build_bandlimited_square(tables_[name], table_size);
    else if (name == "triangle") build_bandlimited_triangle(tables_[name], table_size);
    else build_sine(tables_[name], table_size);      // fallback 
}

bool WavetableManager::has_table(const std::string& name) {
    std::lock_guard<std::mutex> lock(mutex_);
    return tables_.count(name) > 0;
}

std::vector<double> WavetableManager::render(
    const std::string& name,
    double start_phase,
    double phase_inc,
    int num_frames,
    double amplitude,
    double phase_offset
) {
    std::vector<double> table_copy;

    {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!tables_.count(name)) return std::vector<double>(num_frames, 0.0);

        table_copy = tables_[name];
    }

    int N = (int)table_copy.size();

    std::vector<double> out(num_frames);

    double ph0 = start_phase + phase_offset;
    ph0 -= std::floor(ph0);

    // #pragma omp parallel for 
    for (int i = 0; i < num_frames; ++i) {
        double ph = ph0 + i * phase_inc;
        ph -= std::floor(ph);
        out[i] = amplitude * lookup_linear(table_copy, ph);
    }

    return out;
}