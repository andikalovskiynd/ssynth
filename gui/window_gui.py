from PyQt6.QtWidgets import QMainWindow, QPushButton, QLabel, QVBoxLayout
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPixmap
from knob import Knob
from button import Button

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SSYNTH GUI PROTOTYPE")
        self.setFixedSize(QSize(1280, 720))

        self.background = QLabel(self)
        pixmap = QPixmap("assets/background/background.png")
        self.background.setPixmap(pixmap)
        self.background.setScaledContents(True) 
        self.background.setGeometry(0, 0, 1280, 720)

        self.knob1 = Knob(self, x=400, y=300, size=36, total_frames=181)
        self.knob1.valueChanged.connect(self.knob_moved)

        btn = Button(parent=self, x=100, y=100, width=120, height=60,
                   unpressed_path="assets/button/unpressed.png",
                   pressed_path="assets/button/pressed.png",
                   hover_path="assets/button/hover.png",
                   toggle=True)
        btn.clicked.connect(lambda: print("Button clicked"))
        btn.toggled.connect(lambda state: print("Button toggled:", state))

    def knob_moved(self, val):
        print(f"Knob value: {val}")

    def on_generate_saw(self):
        print("GENERATED")