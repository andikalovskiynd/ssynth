import numpy as np
from PyQt6.QtWidgets import QMainWindow, QWidget
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import QTimer
from OpenGL.GL import *

import spectrogram_vis_cpp 

FFT_SIZE = 1024
NUM_BINS = FFT_SIZE // 2 + 1
HISTORY_LENGTH = 100

class SpectrogramWidget(QOpenGLWidget):
    def __init__(self, data: np.ndarray, sample_rate: float, parent=None):
        super().__init__(parent)
        self.data = data
        self.sample_rate = sample_rate

        self.spectrum_history = np.zeros((HISTORY_LENGTH, NUM_BINS), dtype=np.float32)
        self.history_index = 0

        self.data_offset = 0.0
        self.frame_length = FFT_SIZE

        self.hop_size = FFT_SIZE // 2   # how much samples is hopping per each frame

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_spectrogram)
        self.timer.start(100)

    def InitializeGL(self):
        glClearColor(0.15, 0.15, 0.15, 1.0)
        glEnable(GL_TEXTURE_2D)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

    def update_spectrogram(self):
        end_idx = int(self.data_offset + self.frame_length)

        if end_idx >= len(self.data):
            self.timer.stop()
            return
        
        segment = self.data[int(self.data_offset) : end_idx]

        magnitudes = 