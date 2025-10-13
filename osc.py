import numpy as np 
import math 

# ================================
# =         Oscillator           =
# ================================

class Oscillator:
    def __init__(self, wave_type='sine', freq=440.0, amplitude=1.0, sample_rate=44100):
        self.wave_type = wave_type
        self.freq = freq
        self.amplitude = amplitude
        self.sample_rate = sample_rate
        self.phase = 0.0    # normalized phase in [0.0, 1.0)
    
    def process(self, num_frames: int):
        """ 
        Generates array with num_frames samples
            It is practically convinient to keep phase not in seconds but in normalized form, 
            in [0,1) as fraction of cycle. So every step is: dph = f / f_s 
            And sine, for example is x[n] = Asin(2pi * ph_n), ph_n = ph_n-1 + dph.
        """

        # phase increment per sample (fraction of cycle)
        phase_inc = self.freq / self.sample_rate

        # array of phases for each sample
        phases = (self.phase + phase_inc * np.arange(num_frames)) % 1.0

        if self.wave_type == 'sine':
            out = np.sin(2 * np.pi * phases)   # x[n] = A * sin (2pi * ph_n), ph_n in [0,1)

        elif self.wave_type == 'square':
            out = np.sign(np.sin(2 * np.pi * phases))  # x[n] = A * sign (sine)

        elif self.wave_type == 'saw':
            out = 2.0 * (phases - 0.5)    # x[n] = 2(ph_n - 0.5)

        elif self.wave_type == 'triangle':
            out = 2.0 * np.abs(2.0 * (phases - np.floor(phases + 0.5))) - 1.0    # x[n] = 2 * abs(2(ph_n - floor(ph_n + 0.5))) - 1

        else:
            out = np.zeros(num_frames)

        # update phase for next calls 
        self.phase = (self.phase + phase_inc * num_frames) % 1.0

        return self.amplitude * out


# ================================
# =            Voice             =
# ================================

class Voice:
    """
    One voice (up to 3 oscs)
    """
    def __init__(self, freq: float, sample_rate=44100):
        self.oscillators = [
            Oscillator(freq=freq, sample_rate=sample_rate),
            Oscillator(freq=freq, sample_rate=sample_rate),
            Oscillator(freq=freq, sample_rate=sample_rate)
        ]
        self.is_active = True
    
    def set_waveforms(self, waveforms):
        """ Set waveform for each osc """
        for osc, wf in zip(self.oscillators, waveforms):
            osc.wave_type = wf
    
    def set_amplitudes(self, amps):
        """ Set amplitude for each osc """
        for osc, amp in zip(self.oscillators, amps):
            osc.amplitude = amp

    def process(self, num_frames):
        """ Sum signals from all of oscs """
        if not self.is_active:
            return np.zeros(num_frames)
        mix = sum(osc.process(num_frames) for osc in self.oscillators)
        return mix / len(self.oscillators)
    

# ================================
# =         Voice Engine         =
# ================================
    
class VoiceEngine:
    """ Manages active voices """
    def __init__(self, max_voices=8, sample_rate=44100):
        self.voices = []
        self.max_voices = max_voices
        self.sample_rate = sample_rate 

    def note_on(self, freq):
        """ Add new voice """
        if len(self.voices) >= self.max_voices:
            self.voices.pop()
        v = Voice(freq=freq, sample_rate=self.sample_rate)
        self.voices.append(v)

    def note_off(self, freq):
        """ Delete active voice with specified frequency """
        for v in self.voices:
            if abs(v.oscillators[0].freq - freq) < 1e-3:
                v.is_active = False

    def process(self, num_frames):
        """ Sum signals from all of active voices """
        if not self.voices:
            return np.zeros(num_frames)
        mix = sum(v.process(num_frames) for v in self.voices)
        return mix / len(self.voices)