import numpy as np

class Envelope:
    def __init__(self, attack=0.01, decay=0.2, sustain=0.7, release=0.5, sample_rate=44100, sustain_time=None):
        self.attack = attack
        self.decay = decay 
        self.sustain = sustain
        self.release = release
        self.sustain_time = sustain_time  # if 'None', sustain indefinitely; if set, auto-release after this time
        self.sample_rate = sample_rate
        self.reset()

    def reset(self):
        """Reset envelope to initial state"""
        self.state = 'idle'
        self.level = 0.0
        self.sample_count = 0
        self.sustain_sample_count = 0
        self.note_triggered = False

    def note_on(self):
        """Trigger the envelope to start from attack phase"""
        self.state = 'attack'
        self.level = 0.0
        self.sample_count = 0
        self.sustain_sample_count = 0
        self.note_triggered = True

    def note_off(self):
        """Trigger the envelope to enter release phase"""
        if self.state != 'idle':
            self.state = 'release'
            self.sample_count = 0

    def process(self, audio_signal):
        """Apply envelope to audio signal with proper ADSR timing"""
        audio_signal = np.array(audio_signal, dtype=np.float32)
        
        # again - stereo or mono
        if audio_signal.ndim == 1:
            num_frames = len(audio_signal)
            num_channels = 1
        else:
            num_frames, num_channels = audio_signal.shape
        
        output = np.zeros_like(audio_signal)
        
        for i in range(num_frames):
            # auto-trigger if not yet triggered and we have input signal
            if not self.note_triggered and np.any(np.abs(audio_signal[i]) > 1e-6):
                self.note_on()
            
            if self.state == 'attack':
                if self.attack > 0:
                    attack_samples = int(self.attack * self.sample_rate)
                    if attack_samples > 0:
                        self.level = self.sample_count / attack_samples
                        if self.level >= 1.0:
                            self.level = 1.0
                            self.state = 'decay'
                            self.sample_count = 0
                    else:
                        self.level = 1.0
                        self.state = 'decay'
                        self.sample_count = 0
                else:
                    self.level = 1.0
                    self.state = 'decay'
                    self.sample_count = 0
            
            elif self.state == 'decay':
                if self.decay > 0:
                    decay_samples = int(self.decay * self.sample_rate)
                    if decay_samples > 0:
                        decay_progress = self.sample_count / decay_samples
                        if decay_progress >= 1.0:
                            self.level = self.sustain
                            self.state = 'sustain'
                            self.sample_count = 0
                            self.sustain_sample_count = 0  
                        else:
                            self.level = 1.0 - decay_progress * (1.0 - self.sustain)
                    else:
                        self.level = self.sustain
                        self.state = 'sustain'
                        self.sample_count = 0
                        self.sustain_sample_count = 0
                else:
                    self.level = self.sustain
                    self.state = 'sustain'
                    self.sample_count = 0
                    self.sustain_sample_count = 0
            
            elif self.state == 'sustain':
                self.level = self.sustain
                
                # if sustain_time is set, auto-trigger release after that duration
                if self.sustain_time is not None:
                    sustain_samples = int(self.sustain_time * self.sample_rate)
                    if self.sustain_sample_count >= sustain_samples:
                        self.note_off()
                    self.sustain_sample_count += 1
            
            elif self.state == 'release':
                if self.release > 0:
                    release_samples = int(self.release * self.sample_rate)
                    if release_samples > 0:
                        release_progress = self.sample_count / release_samples
                        if release_progress >= 1.0:
                            self.level = 0.0
                            self.state = 'idle'
                            self.sample_count = 0
                        else:
                            start_level = getattr(self, '_release_start_level', self.sustain)
                            self.level = start_level * (1.0 - release_progress)
                    else:
                        self.level = 0.0
                        self.state = 'idle'
                        self.sample_count = 0
                else:
                    self.level = 0.0
                    self.state = 'idle'
                    self.sample_count = 0
            
            elif self.state == 'idle':
                self.level = 0.0
            
            if self.state == 'release' and self.sample_count == 0:
                self._release_start_level = self.level
            
            # apply envelope to audio signal
            if audio_signal.ndim == 1:
                output[i] = audio_signal[i] * self.level
            else:
                output[i] = audio_signal[i] * self.level
            
            # increment sample counter for timing
            if self.state != 'idle' and self.state != 'sustain':
                self.sample_count += 1
        
        return output