import numpy as np
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import QTimer
from OpenGL.GL import *
from PyQt6.QtGui import QPainter, QColor, QFont

HISTORY_LENGTH = 200     
FPS = 60               

def create_magma_lut():
    x = np.linspace(0, 1, 256)
    colors = np.zeros((256, 4), dtype=np.uint8)
    
    # Key colors (normalized 0..1) -> RGB (Magma-like palette)
    stops = [0.0, 0.1, 0.2, 0.35, 0.5, 0.7, 0.9, 1.0]
    rgb_stops = np.array([
        [0, 0, 0],       # Black
        [40, 0, 40],     # Dark Violet
        [130, 0, 130],   # Violet
        [200, 20, 90],   # Pink/Red
        [255, 60, 60],   # Red
        [255, 120, 0],   # Orange
        [255, 180, 0],   # Bright Orange
        [255, 255, 200]  # White/Yellow
    ])
    
    for i in range(3):
        colors[:, i] = np.interp(x, stops, rgb_stops[:, i]).astype(np.uint8)
    
    colors[:, 3] = 255 # Alpha = 255 
    return colors

MAGMA_LUT = create_magma_lut()

class SpectrogramWidget(QOpenGLWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.spectrum_history = None
        self.texture_id = None
        self.history_index = 0
        
        self.log_indices = None 
        self.n_bins_src = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_spectrogram)
        self.timer.start(1000 // FPS) 

    def initializeGL(self):
        glClearColor(0.05, 0.05, 0.05, 1.0)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        
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
        if not self.engine:
            return

        # Get raw magnitudes from engine
        raw_magnitudes = np.array(self.engine.get_spectrum(), dtype=np.float32)
        if raw_magnitudes.size == 0:
            return

        n_src = raw_magnitudes.size
        
        # Init buffers
        if self.spectrum_history is None or self.n_bins_src != n_src:
            self.n_bins_src = n_src
            # Logarithmic stretching
            self.n_bins_dst = n_src 
            
            self.spectrum_history = np.zeros((HISTORY_LENGTH, self.n_bins_dst, 4), dtype=np.uint8)
            
            # Precalculate for log stretching
            self.log_indices = np.geomspace(1, n_src - 1, num=self.n_bins_dst)

        # Resampling by log. This step allows to stretch low fq and shrink high
        log_spectrum = np.interp(self.log_indices, np.arange(n_src), raw_magnitudes)

        # LUT painting
        indices = (log_spectrum * 255).astype(np.uint8)
        colored_spectrum = MAGMA_LUT[indices]

        self.spectrum_history[self.history_index, :] = colored_spectrum
        self.history_index = (self.history_index + 1) % HISTORY_LENGTH
        
        self.update()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        if self.spectrum_history is None: return 
        
        
        to_draw = np.roll(self.spectrum_history, -self.history_index, axis=0)
        
        # History (Time) -> X (Width)
        # Frequency      -> Y (Height)
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
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(255, 255, 255, 120))
        painter.setFont(QFont("Arial", 8))
        
        w = self.width()
        h = self.height()

        top_padding = 12    
        bottom_padding = 5 
        draw_h = h - top_padding - bottom_padding
        
        min_freq = 21.5 
        max_freq = 22050.0
        
        log_min = np.log10(min_freq)
        log_max = np.log10(max_freq)
        log_range = log_max - log_min

        markers = [30, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
        
        for freq in markers:
            if freq < min_freq or freq > max_freq: continue

            val_norm = (np.log10(freq) - log_min) / log_range
            
            # To pixels including padding
            y = int(top_padding + draw_h * (1.0 - val_norm))
            
            text = f"{freq/1000:.0f}k" if freq >= 1000 else f"{freq}"
            
            # Line
            painter.setPen(QColor(255, 255, 255, 40))
            painter.drawLine(0, y, w, y)
            
            # Text
            painter.setPen(QColor(255, 255, 255, 150))
            painter.drawText(5, y - 2, text)

        painter.end()