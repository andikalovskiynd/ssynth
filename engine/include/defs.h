#pragma once

// Global parameters
static const int MAX_VOICES = 16;
static const int VISUALIZATION_BUFFER_SIZE = 44100;
static const int FFT_SIZE = 2048;

// ID for all of the knobs which are available in python 
enum ParamID {
    // Master 
    MASTER_VOL,
    
    // Oscillator 1 
    OSC1_TYPE,      // (int) ID if table
    OSC1_PITCH,     // Semitones (-12..+12)
    OSC1_DETUNE,    // Fine tune
    OSC1_MIX,       // Volume
    
    // Oscillator 2 
    OSC2_TYPE,
    OSC2_PITCH,
    OSC2_DETUNE,
    OSC2_MIX,

    // Oscillator 3
    OSC3_TYPE,
    OSC3_PITCH,
    OSC3_DETUNE,
    OSC3_MIX,

    // Filter
    FILTER_CUTOFF,  // Hz
    FILTER_RES,     // Resonance (0..1)
    FILTER_TYPE,    // LowPass, HighPass etc.
    FILTER_ENV_AMT, // Envelope amplitude

    // Amp Envelope (ADSR)
    AMP_ATTACK,
    AMP_DECAY,
    AMP_SUSTAIN,
    AMP_RELEASE,

    // Filter Envelope (ADSR) 
    FILT_ATTACK,
    FILT_DECAY,
    FILT_SUSTAIN,
    FILT_RELEASE,
    
    // Service value
    PARAM_COUNT
};