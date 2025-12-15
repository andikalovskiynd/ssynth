import numpy as np
from PyQt6.QtWidgets import QMainWindow, QWidget
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import QTimer
from OpenGL.GL import *
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import QPointF

import sys
from pathlib import Path
import math

project_root = Path(__file__).resolve().parents[4]
build_path = project_root / "build"
sys.path.insert(0, str(build_path))

try:
    import spectrogram_vis_cpp as spectrogram_vis_cpp 
    
    if not spectrogram_vis_cpp.init_fftw():
        res = spectrogram_vis_cpp.init_fftw()
        print(f"PYTHON RECEIVED: {res} (Type: {type(res)})")
        raise Exception("1. FFTW initialization failed")
    
    SPECTROGRAM_CPP_AVAILABLE = True
except ImportError as e:
    print(f"ERROR: Could not import spectrogram_cpp. Spectrogram will be disabled. ({e})")
    SPECTROGRAM_CPP_AVAILABLE = False
except Exception as e:
    print(f"ERROR: FFTW setup failed. {e}. (except)")
    SPECTROGRAM_CPP_AVAILABLE = False

FFT_SIZE = 1024
HISTORY_LENGTH = 100
GLOBAL_MIN_LOG = -8.5
GLOBAL_MAX_LOG = 3.0
MB_COUPLING = 0.01       # Coefficient of connection between multibands 
NUM_BINS = 1025         # As (N / 2) + 1 in FFT

# --------------------------------------------------- Helping functions

# Define logarithmic borders
# Approximately, this is an octave-based fraction
# Starting from bin 1 (we will ignore bin 0 further)
# 12 bands, approx from 33Hz to 22.05kHz (as sample rate is 44.1kHz)
def get_log_bands(NUM_BINS, num_bands=12):
    # As said, using bins from 1 to num_bins - 1
    max_bin_idx = NUM_BINS - 1
    log_idxs = np.geomspace(1, max_bin_idx, num=num_bands + 1)
    bands_limits = np.unique(np.round(log_idxs).astype(int))

    # Additive check that 1 is start and 1024 is end
    if bands_limits[0] != 1:
        bands_limits = np.insert(bands_limits, 0, 1)
    if bands_limits[-1] != max_bin_idx:
        bands_limits = np.append(bands_limits, max_bin_idx)

    bands_limits = np.unique(bands_limits)  # Delete 0 bin and dublicates if they managed to get in 
    return bands_limits[bands_limits >= 1]
 
    # Magma (purple-yellow) colormap for better perception 
def magma(value):
    value = np.clip(value, 0.0, 1.0)

    # Key colors for future interpolation
    colors = [
        (0,   0,   0),    # 0.0 - Black
        (40,  0,   40),   # 0.1 - Very Dark Violet
        (130, 0,   130),  # 0.2 - Violet
        (200, 20,  90),   # 0.35 - Deep Pink-Red ⚠️ Сдвиг!
        (255, 60,  60),   # 0.5 - Red ⚠️ Сдвиг!
        (255, 120, 0),    # 0.7 - Orange ⚠️ Сдвиг!
        (255, 180, 0),    # 0.9 - Bright Orange
        (255, 255, 200)   # 1.0 - Light Yellow-White
    ]

    stops = [0.0, 0.1, 0.2, 0.35, 0.5, 0.7, 0.9, 1.0]

    # Find where to fall and interpolate
    idx = 0
    while idx < len(stops) - 1 and value >= stops[idx+1]:
        idx += 1
    # Or if it is exact stop
    if idx == len(stops) - 1:
        return colors[idx] + (255,)     # Add alpha channel
        
    # Linear interpolation
    start_color = colors[idx]
    end_color = colors[idx+1]
    start_stop = stops[idx]
    end_stop = stops[idx+1]

    # Avoid division by 0
    if end_stop == start_stop:
        return start_color + (255,)
        
    factor = (value - start_stop) / (end_stop - start_stop)

    # And finally
    r = int(start_color[0] + factor * (end_color[0] - start_color[0]))
    g = int(start_color[1] + factor * (end_color[1] - start_color[1]))
    b = int(start_color[2] + factor * (end_color[2] - start_color[2]))

    return (r, g, b, 255)

# -------------------------------------------------------------------------

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
        self.hop_size = FFT_SIZE // 2   # how much samples is hopping per each frame

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_spectrogram)
        self.timer.start(50)    # ~20 FPS

    def initializeGL(self):
        glClearColor(0.15, 0.15, 0.15, 1.0)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)

        # Create blank texture
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        # Interpolation parameteres 
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        # To make texture don't repeat on edges
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, HISTORY_LENGTH, NUM_BINS, 0, GL_RGBA, GL_UNSIGNED_BYTE, None) # Changed from GL_LUMINANCE

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def update_spectrogram(self):
        end_idx = int(self.data_offset + self.frame_length)
        if end_idx >= len(self.data):
            self.timer.stop()
            return
        
        segment = self.data[int(self.data_offset) : end_idx]

        # 1. Input audio check
        print(f"DEBUG AUDIO: Min={segment.min():.4f}, Max={segment.max():.4f}, Mean={segment.mean():.4f}")

        # Start an operation
        magnitudes = spectrogram_vis_cpp.calculate_spectrum_fftw(segment)

        # 2. C++ returns check
        print(f"DEBUG MAGS: Min={magnitudes.min():.4e}, Max={magnitudes.max():.4e}, MaxIdx={np.argmax(magnitudes)}")

        # Because spectrum_history now must contain color information too
        if self.spectrum_history is None or self.spectrum_history.shape[2] != 4:
            real_bins = magnitudes.shape[0]
            print(f"DEBUG: C++ bins: {real_bins}. Re-initializing history for RGBA.")
            self.spectrum_history = np.zeros((HISTORY_LENGTH, real_bins, 4), dtype=np.uint8)

        #--------------------------- Multiband Normalization
        # Due to problems which occurs in one-band approach when dynamic range is too big, 
        # we have to process few blocks of origin frequencies, at the same time, considering 
        # global dynamic range, because otherwise, spectrogram will become a graph that shows
        # 12 separate segments, each with its own dynamic range 
            
        log_magnitudes = np.log10(magnitudes + 1e-9)

        # 3. Check after log
        print(f"DEBUG LOGS: Min={log_magnitudes.min():.4f}, Max={log_magnitudes.max():.4f}")

        # Make a mask with all the bins except 0
        bands_limits = get_log_bands(NUM_BINS=NUM_BINS, num_bands=12)
        normalized_spectrum = np.zeros_like(log_magnitudes)
        normalized_spectrum[0] = 0.0    # DC bin should always be black 

        for i in range(len(bands_limits) - 1):
            start_bin = bands_limits[i]
            end_bin = bands_limits[i+1]

            band_mags = log_magnitudes[start_bin:end_bin]
            if len(band_mags) == 0:
                continue

            local_max = band_mags.max()
            local_min = band_mags.min()

            # Coupling for defining the formative range (min/max)
            # If MB_Cupling = 1.0, norm_max = GLOBAL_MAX_LOG, else if 0.0, norm_max = local_max
            norm_max = (MB_COUPLING * GLOBAL_MAX_LOG) + ((1 - MB_COUPLING) * local_max)

            # Same for norm_min
            norm_min = (MB_COUPLING * GLOBAL_MIN_LOG) + ((1 - MB_COUPLING) * local_min)

            if norm_max <= norm_min:
                norm_max = norm_min + 0.1

            norm_band = (band_mags - norm_min) / (norm_max - norm_min)
            normalized_spectrum[start_bin:end_bin] = np.clip(norm_band, 0.0, 1.0)

        # Make colors from "normalized_spectrum"'s values 
        colored_spectrum = np.zeros((normalized_spectrum.shape[0], 4), dtype = np.uint8)
        for i, val in enumerate(normalized_spectrum):
            r, g, b, a = magma(val)
            colored_spectrum[i] = [r, g, b, a]


        # Check after normalization
        print(f"DEBUG NORM: Avg={normalized_spectrum.mean():.4f}, Max={normalized_spectrum.max():.4f}")

        # Write to buffer and update
        self.spectrum_history[self.history_index, :] = colored_spectrum
        self.history_index = (self.history_index + 1) % HISTORY_LENGTH

        self.data_offset += self.hop_size
        self.update()
        

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)

        if self.spectrum_history is None:
            return 
        
        to_draw = np.roll(self.spectrum_history, -self.history_index, axis=0)
        to_draw = to_draw.transpose(1, 0, 2)

        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        h, w, c = to_draw.shape
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, to_draw)

        # Painting one square with texture
        glColor3f(1.0, 1.0, 1.0)
        glEnable(GL_TEXTURE_2D)

        glBegin(GL_QUADS)
        # Coordinates
        glTexCoord2f(0.0, 0.0); glVertex2f(-1.0, -1.0) # bottom-left
        glTexCoord2f(1.0, 0.0); glVertex2f( 1.0, -1.0) # bottom-right
        glTexCoord2f(1.0, 1.0); glVertex2f( 1.0,  1.0) # up-right
        glTexCoord2f(0.0, 1.0); glVertex2f(-1.0,  1.0) # up-left

        glEnd()
        glDisable(GL_TEXTURE_2D)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(255, 255, 255, 200))
        painter.setFont(QFont("Arial", 5))

        width = self.width()
        height = self.height()
    
        # Rectangle to divide spectrogram and text
        painter.fillRect(0, 0, 28, height, QColor(0, 0, 0))

        # Constants for logarithmic scale
        freq_min = 20.0
        freq_max = self.sample_rate / 2.0
        log_freq_min = np.log10(freq_min)
        log_freq_range = np.log10(freq_max) - log_freq_min
        markers = [50, 100, 200, 400, 800, 1000, 2000, 4000, 8000, 16000, 20000]

        for freq in markers:
            if freq < freq_min:
                continue

            log_freq = np.log10(freq)
            y_norm = (log_freq - log_freq_min) / log_freq_range

            # Invert (0.0 - bottom, 1.0 - upper) and scale
            y_pix = int(height * (1.0 - y_norm))

            x_start = int(width * 0.05)

            # k-s formate
            if freq >= 1000:
                text = f"{freq / 1000.0:.1f} kHz"
            else:
                text = f"{freq} Hz"

            painter.drawText(x_start-20, y_pix + 5, text)

        painter.end()
