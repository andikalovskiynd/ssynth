#include <vector> 
extern "C" {
    // LOW PASS FILTER: Formula: y[n] = y[n-1] + alpha * (x[n] - y[n-1])
    void process_lpf(float* x, float* y, int N, float alpha, float* prev_y) {
        float y_prev = *prev_y;
        for (int i = 0; i < N; ++i) {
            y_prev += alpha * (x[i] - y_prev);
            y[i] = y_prev;
        }
        *prev_y = y_prev;
    }

    // HIGH PASS FILTER: Formula: y[n] = alpha (y[n-1] + x[n] - x[n-1])
    void process_hpf(float* x, float* y, int N, float alpha, float* prev_y) {
        float y_prev = *prev_y;
        float x_prev = 0.0f;
        for (int i = 0; i < N; ++i) {
            y_prev = alpha * (y_prev + x[i] - x_prev);
            y[i] = y_prev;
            x_prev = x[i];
        }
        *prev_y = y_prev;
    }
}