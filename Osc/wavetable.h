#pragma once
#include <vector>
#include <string>
#include <map>
#include <mutex>
#include <cmath>

// Struct for keeping a chain of MIP-levels
struct WavetableSet {
    std::vector<std::vector<double>> mips; 
    int baseSize = 0;
    int numMips = 0;
};

class WavetableManager {
public:
    WavetableManager(int sample_rate);
    ~WavetableManager();

    bool load_wvt(const std::string& name, const std::string& filepath);

    bool has_table(const std::string& name);

    void render(
        const std::string& name,
        double& current_phase, 
        double phase_inc,
        int num_frames,
        double amplitude,
        std::vector<double>& output_buffer
    );

private:
    int sample_rate_;
    std::mutex mutex_;
    std::map<std::string, WavetableSet> tables_;

    inline double lookup_linear(const std::vector<double>& table, double phase);
};