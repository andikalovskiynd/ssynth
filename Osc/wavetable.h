#pragma once
#include <vector>
#include <string> 
#include <unordered_map>
#include <mutex> 

class WavetableManager {
public:
    WavetableManager(int sample_rate = 44100.0);
    ~WavetableManager();

    // Generate standard tables
    void generate_sine(const std::string& name, int table_size);
    void generate_square(const std::string& name, int table_size);
    void generate_saw(const std::string& name, int table_size);
    void generate_triangle(const std::string& name, int table_size);

    // 
    void ensure_table(const std::string& name, int table_size);

    // Render num_frames starting from phase in [0,1), with phase_inc
    std::vector<double> render(
        const std::string& name,
        double start_phase,
        double phase_inc,
        int num_frames,
        double amplitude = 1.0,
        double phase_offset = 0.0
    );

    bool has_table(const std::string& name);

private: 
    int sample_rate_;
    std::unordered_map<std::string, std::vector<double>> tables_;
    std::mutex mutex_;

    // Bandlimited builder prevents aliasing by cutting harmonics to Nyquist / freq pieces
    void build_bandlimited_square(std::vector<double>& table, int table_size);
    void build_bandlimited_saw(std::vector<double>& table, int table_size);
    void build_bandlimited_triangle(std::vector<double>& table, int table_size);

    // Sine wave doesn't need bandlimiting cause it has only one harmonic
    void build_sine(std::vector<double>& table, int table_size);

    // Linear interpolation
    inline double lookup_linear(const std::vector<double>& table, double phase);
};