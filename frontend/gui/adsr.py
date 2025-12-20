from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from frontend.gui.knob import Knob
import ssynth_cpp 

class AdsrPanel(QWidget):
    def __init__(self, parent=None, title="AMP ENVELOPE", engine=None):
        super().__init__(parent)
        self.engine = engine
        
        # Основной лейаут
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.setLayout(layout)
        
        # Заголовок
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl_title, alignment=Qt.AlignmentFlag.AlignCenter)

        # Контейнер для ручек
        knobs_layout = QHBoxLayout()
        knobs_layout.setSpacing(15)
        
        # --- ATTACK (0.001s .. 2.0s) ---
        # Default 0.01
        self.knob_a = self.create_knob("Attack", 0.001, 2.0, 0.01, knobs_layout)
        self.knob_a.valueChanged.connect(lambda v: self.set_param(ssynth_cpp.Params.AMP_ATTACK, v))

        # --- DECAY (0.001s .. 2.0s) ---
        # Default 0.2
        self.knob_d = self.create_knob("Decay", 0.001, 2.0, 0.2, knobs_layout)
        self.knob_d.valueChanged.connect(lambda v: self.set_param(ssynth_cpp.Params.AMP_DECAY, v))

        # --- SUSTAIN (0.0 .. 1.0 Level) ---
        # Default 0.7
        self.knob_s = self.create_knob("Sustain", 0.0, 1.0, 0.7, knobs_layout)
        self.knob_s.valueChanged.connect(lambda v: self.set_param(ssynth_cpp.Params.AMP_SUSTAIN, v))

        # --- RELEASE (0.001s .. 5.0s) ---
        # Default 0.5
        self.knob_r = self.create_knob("Release", 0.001, 5.0, 0.5, knobs_layout)
        self.knob_r.valueChanged.connect(lambda v: self.set_param(ssynth_cpp.Params.AMP_RELEASE, v))
        
        layout.addLayout(knobs_layout)

        # Инициализация значений в движке
        if self.engine:
            self.set_param(ssynth_cpp.Params.AMP_ATTACK, self.knob_a.value)
            self.set_param(ssynth_cpp.Params.AMP_DECAY, self.knob_d.value)
            self.set_param(ssynth_cpp.Params.AMP_SUSTAIN, self.knob_s.value)
            self.set_param(ssynth_cpp.Params.AMP_RELEASE, self.knob_r.value)

    def create_knob(self, label, min_v, max_v, default, parent_layout):
        container = QWidget()
        l = QVBoxLayout()
        container.setLayout(l)
        l.setContentsMargins(0,0,0,0)
        l.setSpacing(5)
        
        k = Knob(container, size=48)
        k.min_value = min_v
        k.max_value = max_v
        k.value = default
        
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #aaa; font-size: 11px;")
        
        l.addWidget(k, alignment=Qt.AlignmentFlag.AlignCenter)
        l.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        parent_layout.addWidget(container)
        return k

    def set_param(self, param_id, value):
        if self.engine:
            self.engine.set_param(param_id, float(value))

    # for preset also
    def get_state(self):
        return {
            "attack": self.knob_a.value,
            "decay": self.knob_d.value,
            "sustain": self.knob_s.value,
            "release": self.knob_r.value
        }

    def set_state(self, state):
        if not state: return
        if "attack" in state: self.knob_a.set_value(state["attack"])
        if "decay" in state: self.knob_d.set_value(state["decay"])
        if "sustain" in state: self.knob_s.set_value(state["sustain"])
        if "release" in state: self.knob_r.set_value(state["release"])