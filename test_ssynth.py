import numpy as np
import soundfile as sf
import sounddevice as sd
import matplotlib.pyplot as plt
import sys
import os
from Osc.osc import Oscillator, Voice, VoiceEngine
from Filter.filter import Filter
from Filter.envelope import Envelope
from gui.visual.visualizer import GLWidget
from misc.logger import Log

qt_plugins = "/Users/cyrep/Documents/python/ENTER/lib/python3.13/site-packages/PyQt6/Qt6/plugins"
os.environ["QT_PLUGIN_PATH"] = qt_plugins

from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import QTimer
from OpenGL.GL import *
from gui.window_gui import MainWindow
from gui.main_gui import main as startgui
from PyQt6.QtCore import QDir
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
GUI_DIR = PROJECT_ROOT / "gui"
QDir.addSearchPath('gui', str(GUI_DIR))
Log.dbg(f"Added Qt search path for 'gui': {GUI_DIR}")

osc1 = Oscillator(wave_type='sine', freq=0.0, amplitude=1.0, detune=0.0, phase_offset=0.0)
osc2 = Oscillator(wave_type='sine', freq=3000.0, amplitude=0.0, detune=0.0, phase_offset=0.0)
osc3 = Oscillator(wave_type='sine', freq=250.0, amplitude=0.0, detune=0.0, phase_offset=0.0)

voice = Voice(freq=880.0)
voice.oscillators = [osc1, osc2, osc3]
voice.set_waveforms(['sine', 'sine', 'sine'])
voice.set_pan(0.0)

engine = VoiceEngine(max_voices=4, master_gain=1.0)
engine.voices.append(voice)

duration = 5.0
num_frames = int(duration * engine.sample_rate)
audio = engine.process(num_frames)

lpf = Filter('lpf')

base_alpha = 0.99
alpha = base_alpha

audio_filtered = lpf.process(audio, alpha=alpha)

env = Envelope(attack=0.01, decay=0.0, sustain=5.0, release=0.19, sustain_time=5.0)
audio_enveloped = env.process(audio_filtered)

if np.max(np.abs(audio)) > 0:
    audio = audio / np.max(np.abs(audio))

sf.write("output_3sine.wav", audio_enveloped, engine.sample_rate)
print("Saved file")

if __name__ == "__main__":
    startgui(data=audio_enveloped, sample_rate=engine.sample_rate)