from PyQt6.QtWidgets import QWidget, QInputDialog
from PyQt6.QtGui import QPainter, QPixmap, QMouseEvent
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

# To make nice looking and at least poorly optimized GUI
class KnobCache:
    _frames = None
    _angle_cache = {}   # cache for similar angles

    @classmethod
    def load_frames(cls, total=181):
        if cls._frames is None:
            cls._frames = []
            for i in range(total):
                pix = QPixmap(f"gui:assets/knob/frame_{i}.png")
                cls._frames.append(pix)

    @classmethod
    def get_frame(cls, value, min_value=0.0, max_value=1.0):
        t = (value - min_value) / (max_value - min_value)
        t = max(0.0, min(1.0, t))
        index = round(t * (len(cls._frames) - 1))

        if index in cls._angle_cache:
            return cls._angle_cache[index]

        frame = cls._frames[index]
        cls._angle_cache[index] = frame
        return frame
    
class Knob(QWidget):
    valueChanged = pyqtSignal(float)

    def __init__(self, parent=None, x=0, y=0, size=256, image_path=None, total_frames=181):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.move(x, y)

        KnobCache.load_frames(total=total_frames)

        self.min_value = 0.0
        self.max_value = 1.0
        self.value = 0.5

        self.last_y = None
        self.sensitivity = 200  # more - smoother

    def set_value(self, val):
        val = max(self.min_value, min(self.max_value, float(val)))
        if self.value != val:
            self.value = val
            self.update()
            self.valueChanged.emit(self.value)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pixmap = KnobCache.get_frame(self.value, self.min_value, self.max_value)
        pixmap = pixmap.scaled(self.width(), self.height(),
                               Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                               Qt.TransformationMode.SmoothTransformation)

        cx = self.width() // 2
        cy = self.height() // 2
        px = pixmap.width() // 2
        py = pixmap.height() // 2

        painter.translate(cx, cy)
        painter.drawPixmap(-px, -py, pixmap)
        painter.resetTransform()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_y = event.position().y()
            event.accept()
        
        elif event.button() == Qt.MouseButton.RightButton:
            #self.schedule_input_dialog()       This is a non-working way to make a dialogue window to set custom
            #                                   parameters to knobs. Need to think better how to do it: TODO
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.schedule_input_dialog()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.last_y is None:
            return
        
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            self.last_y = None
            return

        current_y = event.position().y()
        dy = self.last_y - event.position().y()
        delta = dy / self.sensitivity
        
        # Speed up for large ranges
        rng = self.max_value - self.min_value
        if rng > 10.0: delta *= (rng / 5.0)

        new_value = self.value + delta
        new_value = max(self.min_value, min(self.max_value, new_value))

        if new_value != self.value:
            self.value = new_value
            self.update()
            self.valueChanged.emit(self.value)

        self.last_y = current_y

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_y = None
            event.accept()

    def schedule_input_dialog(self):
        self.last_y = None
        # It allows QT correctly check that click is ended
        QTimer.singleShot(1, self.open_input_dialog)

    def open_input_dialog(self):
        val, ok = QInputDialog.getDouble(
            self, 
            "Set Value", 
            f"Enter value ({self.min_value:.2f} - {self.max_value:.2f}):", 
            value=self.value, 
            min=self.min_value, 
            max=self.max_value, 
            decimals=4 
        )
        if ok:
            self.set_value(val)