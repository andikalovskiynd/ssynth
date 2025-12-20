from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QComboBox
from PyQt6.QtCore import Qt
from frontend.gui.knob import Knob

class OscPanel(QWidget):
    def __init__(self, parent=None, title="OSC 1", engine=None, osc_id=1, wavetables=None):
        super().__init__(parent)
        self.engine = engine
        self.osc_id = osc_id
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(lbl_title, alignment=Qt.AlignmentFlag.AlignCenter)

        # Waveform Selector
        self.combo_wave = QComboBox()
        if wavetables:
            for name, w_id in wavetables.items():
                self.combo_wave.addItem(name, w_id)
        
        self.combo_wave.currentIndexChanged.connect(self.on_wave_change)
        layout.addWidget(self.combo_wave)

        # Knobs Row
        knobs_layout = QHBoxLayout()
                
        # MIX Knob
        self.knob_mix = self.create_knob("Mix", 0.0, 1.0, 1.0 if osc_id==1 else 0.0, knobs_layout)
        self.knob_mix.valueChanged.connect(self.on_mix_change)

        # PITCH Knob (-24 .. +24)
        self.knob_pitch = self.create_knob("Pitch", -24.0, 24.0, 0.0, knobs_layout)
        self.knob_pitch.valueChanged.connect(self.on_pitch_change)

        # DETUNE Knob (-1.0 .. +1.0)
        self.knob_detune = self.create_knob("Fine", -1.0, 1.0, 0.0, knobs_layout)
        self.knob_detune.valueChanged.connect(self.on_detune_change)
        
        layout.addLayout(knobs_layout)
        
        # Initial Apply
        self.on_wave_change(0)

    def create_knob(self, label, min_v, max_v, default, parent_layout):
            container = QWidget()
            l = QVBoxLayout()
            container.setLayout(l)
            l.setContentsMargins(0,0,0,0)
        
            k = Knob(container, size=48)
            k.min_value = min_v
            k.max_value = max_v
            k.value = default
        
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #aaa; font-size: 10px;")
            
            l.addWidget(k, alignment=Qt.AlignmentFlag.AlignCenter)
            l.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)

            parent_layout.addWidget(container)
            
            return k    

    # Callbacks 
    def get_param_ids(self):
        # Return tuple of parameters id depends on osc number
        import ssynth_cpp
        if self.osc_id == 1:
            return (ssynth_cpp.Params.OSC1_TYPE, ssynth_cpp.Params.OSC1_MIX, ssynth_cpp.Params.OSC1_PITCH, ssynth_cpp.Params.OSC1_DETUNE)
        elif self.osc_id == 2:
            return (ssynth_cpp.Params.OSC2_TYPE, ssynth_cpp.Params.OSC2_MIX, ssynth_cpp.Params.OSC2_PITCH, ssynth_cpp.Params.OSC2_DETUNE)
        else:
            return (ssynth_cpp.Params.OSC3_TYPE, ssynth_cpp.Params.OSC3_MIX, ssynth_cpp.Params.OSC3_PITCH, ssynth_cpp.Params.OSC3_DETUNE)

    def on_wave_change(self, idx):
        if not self.engine: return
        wave_id = self.combo_wave.currentData()
        p_type, _, _, _ = self.get_param_ids()
        self.engine.set_param(p_type, float(wave_id))

    def on_mix_change(self, val):
        if not self.engine: return
        _, p_mix, _, _ = self.get_param_ids()
        self.engine.set_param(p_mix, val)

    def on_pitch_change(self, val):
        if not self.engine: return
        _, _, p_pitch, _ = self.get_param_ids()
        self.engine.set_param(p_pitch, val)

    def on_detune_change(self, val):
        if not self.engine: return
        _, _, _, p_detune = self.get_param_ids()
        self.engine.set_param(p_detune, val)

    # For presets
    def get_state(self):
        return {
            "wave_index": self.combo_wave.currentIndex(),
            "mix": self.knob_mix.value,
            "pitch": self.knob_pitch.value,
            "detune": self.knob_detune.value
        }

    def set_state(self, state):
        if not state: return
        
        if "wave_index" in state:
            idx = int(state["wave_index"])
            if 0 <= idx < self.combo_wave.count():
                self.combo_wave.setCurrentIndex(idx)
        
        if "mix" in state: self.knob_mix.set_value(state["mix"])
        if "pitch" in state: self.knob_pitch.set_value(state["pitch"])
        if "detune" in state: self.knob_detune.set_value(state["detune"])