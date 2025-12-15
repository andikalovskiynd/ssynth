import numpy as np
import sys
import os

CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_FILE_DIR))
BUILD_PATH = os.path.join(PROJECT_ROOT, "build")

if os.path.exists(BUILD_PATH) and BUILD_PATH not in sys.path:
    sys.path.append(BUILD_PATH)

WAVETABLE_AVAILABLE = False
try:
    import wavetable_cpp
    wavetable_cpp.init(44100)
    WAVETABLE_AVAILABLE = True
    print(f"DEBUG: Wavetable module loaded.")
except ImportError:
    print(f"WARNING: Wavetable module NOT found in {BUILD_PATH}. Using pure Python (slow).")
except Exception as e:
    print(f"ERROR: Failed to init wavetable module: {e}")

# ================================
# =    Global Resource Manager   =
# ================================

def init_resources():
    if not WAVETABLE_AVAILABLE:
        return

    TABLES_DIR = os.path.join(CURRENT_FILE_DIR, "tables")
    waveforms = ["saw", "square", "triangle", "sine"]
    
    if not os.path.exists(TABLES_DIR):
        print(f" [!] Error: Directory {TABLES_DIR} does not exist.")
        return

    print(f"--- Loading Wavetables from: {TABLES_DIR} ---")
    for name in waveforms:
        filename = f"{name}.wvt"
        filepath = os.path.join(TABLES_DIR, filename)
        
        if os.path.exists(filepath):
            success = wavetable_cpp.load_wvt(name, filepath)
            if success:
                print(f" [+] Loaded: {name}")
            else:
                print(f" [!] C++ failed to parse: {name}")
        else:
            print(f" [-] Not found: {filename}")
    print("--------------------------------------------")

init_resources()


# ================================
# =         Oscillator           =
# ================================

class Oscillator:
    def __init__(self, wave_type='sine', freq=440.0, amplitude=1.0, sample_rate=44100, detune=0.0, phase_offset=0.0):
        self.wave_type = wave_type
        self.freq = freq
        self.amplitude = amplitude
        self.sample_rate = sample_rate
        self.detune = detune 
        
        self.phase = phase_offset % 1.0
        
        self.use_wavetable = False
        self._check_wavetable_availability()

    def set_wave_type(self, wave_type: str):
        self.wave_type = wave_type
        self._check_wavetable_availability()

    def _check_wavetable_availability(self):
        if WAVETABLE_AVAILABLE and wavetable_cpp.has_table(self.wave_type):
            self.use_wavetable = True
        else:
            self.use_wavetable = False

    def process(self, num_frames: int):
        current_freq = self.freq + self.detune
        
        phase_inc = current_freq / self.sample_rate

        # --- C++ FAST PATH ---
        if self.use_wavetable:
            try:
                audio_block, next_phase = wavetable_cpp.render(
                    self.wave_type, 
                    float(self.phase), 
                    float(phase_inc), 
                    int(num_frames), 
                    float(self.amplitude)
                )
                self.phase = next_phase
                return audio_block

            except Exception as e:
                print(f"Error in C++ render: {e}. Fallback to Python.")
                self.use_wavetable = False 

        # --- PYTHON FALLBACK (SLOW) ---
        phases = (self.phase + np.arange(num_frames) * phase_inc) % 1.0
        
        if self.wave_type == 'sine':
            out = np.sin(2 * np.pi * phases)
        elif self.wave_type == 'square':
            out = np.sign(np.sin(2 * np.pi * phases))
        elif self.wave_type == 'saw':
            out = 2.0 * phases - 1.0
        elif self.wave_type == 'triangle':
            out = 2.0 * np.abs(2.0 * (phases - 0.5)) - 1.0
        else:
            out = np.zeros(num_frames)

        self.phase = (self.phase + num_frames * phase_inc) % 1.0
        return self.amplitude * out


# ================================
# =            Voice             =
# ================================

class Voice:
    def __init__(self, freq: float, sample_rate=44100):
        self.freq = freq
        self.sample_rate = sample_rate
        
        self.oscillators = [
            Oscillator(freq=freq, sample_rate=sample_rate)
        ]
        
        self.is_active = True
        self.pan = 0.0 
        self.gain = 1.0 

    def set_waveforms(self, waveforms: list):
        for i, wf in enumerate(waveforms):
            if i < len(self.oscillators):
                self.oscillators[i].set_wave_type(wf)
    
    def set_pan(self, pan: float):
        self.pan = np.clip(pan, -1.0, 1.0)

    def process(self, num_frames: int):
        if not self.is_active or not self.oscillators:
            return np.zeros((num_frames, 2))
        
        mono_mix = np.zeros(num_frames)
        for osc in self.oscillators:
            osc.freq = self.freq 
            mono_mix += osc.process(num_frames)
            
        if len(self.oscillators) > 0:
            mono_mix /= len(self.oscillators)
        
        mono_mix *= self.gain

        # Pan -1 -> Left=1, Right=0
        # Pan  0 -> Left=0.707, Right=0.707
        # Pan  1 -> Left=0, Right=1
        angle = (self.pan + 1.0) * (np.pi / 4.0)
        left_gain = np.cos(angle)
        right_gain = np.sin(angle)

        stereo = np.column_stack((mono_mix * left_gain, mono_mix * right_gain))
        
        return stereo


# ================================
# =         Voice Engine         =
# ================================
    
class VoiceEngine:
    def __init__(self, max_voices=8, sample_rate=44100, master_gain=1.0):
        self.voices = [] 
        self.max_voices = max_voices
        self.sample_rate = sample_rate 
        self.master_gain = master_gain

    def note_on(self, freq, velocity=1.0):
        if len(self.voices) >= self.max_voices:
            self.voices.pop(0) 
            
        v = Voice(freq=freq, sample_rate=self.sample_rate)
        v.gain = velocity
        v.oscillators = [
            Oscillator(wave_type='saw', freq=freq, sample_rate=self.sample_rate),
        ]
        self.voices.append(v)

    def note_off(self, freq):
        for v in self.voices:
            if abs(v.freq - freq) < 0.1:
                v.is_active = False

    def process(self, num_frames):
        self.voices = [v for v in self.voices if v.is_active]

        if not self.voices:
            return np.zeros((num_frames, 2))

        final_mix = np.zeros((num_frames, 2))
        for v in self.voices:
            final_mix += v.process(num_frames)
            
        final_mix *= self.master_gain
        np.clip(final_mix, -1.0, 1.0, out=final_mix)
        
        return final_mix