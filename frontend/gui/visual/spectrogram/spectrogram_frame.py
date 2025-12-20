from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPixmap, QPainter, QColor

class GlassOverlay(QWidget):
    def __init__(self, parent=None, image_path="gui:assets/glass.png"):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents) 
        self.pixmap = QPixmap(image_path)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if not self.pixmap.isNull():
            painter.drawPixmap(self.rect(), self.pixmap)

class SpectrogramFrame(QWidget):
    def __init__(self, spectrogram_widget, parent=None):
        super().__init__(parent)
        
        self.setStyleSheet("""
            SpectrogramFrame {
                background-color: #111; 
                border: 1px solid #333;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10) 
        layout.setSpacing(0)
        
        self.spectrogram = spectrogram_widget
        self.spectrogram.setStyleSheet("border: none;") 
        layout.addWidget(self.spectrogram)

        self.glass = GlassOverlay(self, "gui:assets/glass.png")
        self.glass.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.glass.setGeometry(self.rect())