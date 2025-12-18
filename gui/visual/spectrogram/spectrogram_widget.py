import numpy as np
from PyQt6.QtWidgets import QMainWindow, QWidget
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import QTimer
from OpenGL.GL import *
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import QPointF
from misc.logger import Log

import sys
from pathlib import Path
import math

spectrogram_cpp = None
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parents[1] if "ssynth" in str(current_dir) else current_dir.parent 
build_path = project_root / "build"

if str(build_path) not in sys.path:
    sys.path.insert(0, str(build_path))

SPECTROGRAM_CPP_AVAILABLE = False
try:
    import spectrogram_cpp as spectrogram_vis_cpp
    SPECTROGRAM_CPP_AVAILABLE = True

except ImportError as e:
    Log.err(f"Spectrogram CPP not found: {e}")
except Exception as e:
    Log.err(f"Spectrogram init failed: {e}")

FFT_SIZE = 2048 
HISTORY_LENGTH = 200
NUM_BINS = FFT_SIZE // 2 + 1 

# Vectorized Colormap (LUT)
def create_magma_lut():
    # Creating table of colours (256 values)
    x = np.linspace(0, 1, 256)
    colors = np.zeros((256, 4), dtype=np.uint8)
    
    # Key colors (normalized 0..1) -> RGB
    stops = [0.0, 0.1, 0.2, 0.35, 0.5, 0.7, 0.9, 1.0]
    # RGB values
    rgb_stops = np.array([
        [0, 0, 0],
        [40, 0, 40],
        [130, 0, 130],
        [200, 20, 90],
        [255, 60, 60],
        [255, 120, 0],
        [255, 180, 0],
        [255, 255, 200]
    ])
    
    # Interpolate for each channel
    for i in range(3):
        colors[:, i] = np.interp(x, stops, rgb_stops[:, i]).astype(np.uint8)
    
    colors[:, 3] = 255 # Alpha
    return colors

MAGMA_LUT = create_magma_lut()

class SpectrogramWidget(QOpenGLWidget):
    def __init__(self, data: np.ndarray, sample_rate: float, parent=None):
        super().__init__(parent)
        self.data = data
        self.sample_rate = sample_rate
        self.spectrum_history = None
        self.texture_id = None
        self.history_index = 0
        self.data_offset = 0.0
        
        self.frame_length = FFT_SIZE
        # 50% overlap for smoothness
        self.hop_size = FFT_SIZE // 4   

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_spectrogram)
        self.timer.start(30) # ~30 FPS

    def initializeGL(self):
        glClearColor(0.1, 0.1, 0.1, 1.0)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        # Linear to smooth pixels
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def update_spectrogram(self):
        if not SPECTROGRAM_CPP_AVAILABLE:
            return

        end_idx = int(self.data_offset + self.frame_length)
        if end_idx >= len(self.data):
            self.timer.stop()
            return
        
        segment = self.data[int(self.data_offset) : end_idx]
        
        magnitudes = spectrogram_vis_cpp.calculate_spectrum_fftw(segment)


        if self.spectrum_history is None:
            self.spectrum_history = np.zeros((HISTORY_LENGTH, len(magnitudes), 4), dtype=np.uint8)

        # Convert to dB
        spect_db = 20 * np.log10(magnitudes + 1e-9)

        # Normalize
        min_db = -100.0
        max_db = 0.0
        
        normalized = (spect_db + 100.0) / 100.0
        normalized = np.clip(normalized, 0.0, 1.0)
        normalized[0] = 0.0
        
        # Logarithmic resample
        # New array where lower fq have more values
        n_src = len(normalized)
        n_dst = n_src 
        
        # Logarithmic indicies scale
        # From bin 1 (43Hz) to bin N (22kHz)
        log_indices = np.geomspace(1, n_src - 1, num=n_dst)
        
        log_spectrum = np.interp(log_indices, np.arange(n_src), normalized)
        
        indices = (log_spectrum * 255).astype(np.uint8)
        colored_spectrum = MAGMA_LUT[indices]

        self.spectrum_history[self.history_index, :] = colored_spectrum
        self.history_index = (self.history_index + 1) % HISTORY_LENGTH
        self.data_offset += self.hop_size
        self.update()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        if self.spectrum_history is None: return 
        
        to_draw = np.roll(self.spectrum_history, -self.history_index, axis=0)
        to_draw = to_draw.transpose(1, 0, 2) 
        
        h, w, c = to_draw.shape
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, to_draw)

        glEnable(GL_TEXTURE_2D)
        glColor3f(1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(-1.0, -1.0)
        glTexCoord2f(1.0, 0.0); glVertex2f( 1.0, -1.0)
        glTexCoord2f(1.0, 1.0); glVertex2f( 1.0,  1.0)
        glTexCoord2f(0.0, 1.0); glVertex2f(-1.0,  1.0)
        glEnd()
        glDisable(GL_TEXTURE_2D)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QColor(255, 255, 255, 150))
        painter.setFont(QFont("Arial", 8))
        
        w = self.width()
        h = self.height()
        
        nyquist = self.sample_rate / 2
        markers = [0, 1000, 2000, 5000, 10000, 15000, 20000]
        
        for freq in markers:
            if freq > nyquist: continue
            
            pos_norm = freq / nyquist
            
            y = int(h * (1.0 - pos_norm))
            
            painter.drawText(5, y + 4, f"{freq/1000:.1f}k" if freq >= 1000 else str(freq))
            painter.drawLine(35, y, 45, y)
            
        painter.end()