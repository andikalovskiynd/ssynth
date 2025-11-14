from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPixmap, QPainter, QMouseEvent
from PyQt6.QtCore import pyqtSignal, Qt

class Button(QWidget):
    clicked = pyqtSignal()
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None, x=0, y=0, width=100, height=50,
                 unpressed_path = "assets/button/unpressed.png",
                 pressed_path = "assets/button/pressed.png",
                 hover_path = "assets/button/hover.png",
                 toggle = False):
        super().__init__(parent)
        self.setGeometry(x, y, width, height)

        self.image_unpressed = QPixmap(unpressed_path).scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_pressed = QPixmap(pressed_path).scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_hover = QPixmap(hover_path).scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self.toggle = toggle
        self.is_pressed = False
        self.is_hover = False
    
    def paintEvent(self, event):
        painter = QPainter(self)
        if self.is_pressed:
            painter.drawPixmap(0, 0, self.image_pressed)
        elif self.is_hover:
            painter.drawPixmap(0, 0, self.image_hover)
        else: 
            painter.drawPixmap(0, 0, self.image_unpressed)

    def enterEvent(self, event):
        self.is_hover = True
        self.update()

    def leaveEvent(self, event):
        self.is_hover = False
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.toggle:
                self.is_pressed = not self.is_pressed
                self.toggled.emit(self.is_pressed)
            else:
                self.is_pressed = True
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.toggle:
                self.is_pressed = False
                self.clicked.emit()
            self.update()