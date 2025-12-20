import numpy as np 
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import QTimer
from OpenGL.GL import *

# This module is not working really well so it needs to be refactored or even deleted, TODO

class GLWidget(QOpenGLWidget):
    def __init__(self, data, sample_rate):
        super().__init__()
        self.data = data
        self.sample_rate = sample_rate
        self.offset = 0.0
        self.speed = 0.000025    # less - slower
        self.total_length = len(data)
        self.total_frames_shown = 0

        if len(data.shape) > 1:
            self.data = data[:,0]   # choose left channel if sound is stereo

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(16)    # ~60 fps

    def initializeGL(self):
        glClearColor(0.15, 0.15, 0.15, 1.0)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(1.0)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # setka
        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_LINES)
        for x in np.linspace(-1, 1, 11):
            glVertex2f(x, -1)
            glVertex2f(x, 1)
        for y in np.linspace(-1, 1, 9):
            glVertex2f(-1, y)
            glVertex2f(1, y)
        glEnd()

        # wave itself
        N = 1024

        # using the interpolation for anti-aliasing effect
        ind = (np.arange(N) + self.offset) % len(self.data)
        i0 = np.floor(ind).astype(int)
        i1 = (i0 + 1) % len(self.data)
        frac = ind - i0
        segment = self.data[i0] * (1 - frac) + self.data[i1] * frac

        # normalize the amplitude
        loc_amp = np.max(np.abs(self.data))
        if loc_amp > 0:
            segment = segment / loc_amp

        glDisable(GL_LINE_SMOOTH)
        # Layers with lightning imitation
        # layer one
        glColor4f(0.76, 0.89, 1.0, 0.75)
        glLineWidth(16.0)
        glBegin(GL_LINE_STRIP)
        for i, y in enumerate(segment):
            x = (i / N) * 2 - 1     # normalize x in [-1,1]
            glVertex2f(x, y * 0.8)
        glEnd()

        # layer two
        glColor4f(0.5, 0.7, 1.0, 0.3) 
        glLineWidth(12.0) 
        glBegin(GL_LINE_STRIP)
        for i, y in enumerate(segment):
            x = (i / N) * 2 - 1
            glVertex2f(x, y * 0.8)
        glEnd()

        #layer 3 
        glColor4f(0.6, 0.8, 1.0, 0.6) 
        glLineWidth(3.0) 
        glBegin(GL_LINE_STRIP)
        for i, y in enumerate(segment):
            x = (i / N) * 2 - 1
            glVertex2f(x, y * 0.8)
        glEnd()

        glEnable(GL_LINE_SMOOTH)

        # layer 4 - main 
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glLineWidth(1.5) 
        glBegin(GL_LINE_STRIP)
        for i, y in enumerate(segment):
            x = (i / N) * 2 - 1
            glVertex2f(x, y * 0.8)
        glEnd()

    def update_frame(self):
        frame_shift = self.speed * self.total_length

        if self.offset + frame_shift >= self.total_length:
            self.timer.stop()
            self.offset = self.total_length - 1
        
        else: 
            self.offset += frame_shift

        self.update()

class MainWindow(QMainWindow):
    def __init__(self, data, sample_rate):
        super().__init__()
        self.setWindowTitle("Waveform Visualizer")
        self.setGeometry(300, 200, 800, 400)
        self.gl_widget = GLWidget(data, sample_rate)
        self.setCentralWidget(self.gl_widget)