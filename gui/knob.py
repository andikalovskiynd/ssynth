from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal

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
        """
        t = max(min(value, max_value), min_value)
        index = round(t * (len(cls._frames) - 1))

        if index in cls._angle_cache:
            return cls._angle_cache[index]

        frame = cls._frames[index]
        cls._angle_cache[index] = frame
        return frame
        """
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
        self.value_ = 0.5

        self.last_y = None
        self.sensitivity = 200  # more - smoother

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        pixmap = KnobCache.get_frame(self.value_, self.min_value, self.max_value)
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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_y = event.position().y()

    def mouseMoveEvent(self, event):
        if self.last_y is None:
            return

        dy = self.last_y - event.position().y()
        delta = dy / self.sensitivity

        new_value = self.value_ + delta
        new_value = max(self.min_value, min(self.max_value, new_value))

        if new_value != self.value_:
            self.value_ = new_value
            self.update()
            self.valueChanged.emit(self.value_)

        self.last_y = event.position().y()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_y = None