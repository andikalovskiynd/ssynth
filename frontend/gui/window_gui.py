from PyQt6.QtWidgets import QMainWindow, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QFrame, QFileDialog, QMessageBox, QPushButton
from PyQt6.QtGui import QPixmap, QKeyEvent
from PyQt6.QtCore import Qt

from frontend.gui.visual.spectrogram.spectrogram_widget import SpectrogramWidget
from frontend.gui.osc_panel import OscPanel
from frontend.gui.adsr import AdsrPanel 
from frontend.gui.visual.spectrogram.spectrogram_frame import SpectrogramFrame

import json
import os
from pathlib import Path

class MainWindow(QMainWindow):
    def __init__(self, engine, wavetables, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.wavetables = wavetables
        self.active_keys = {}       # Needed to avoid stucking notes

        self.setWindowTitle("SSYNTH")
        self.setFixedSize(1280, 720) 

        self.background = QLabel(self)
        pixmap = QPixmap("gui:assets/background/background.png")
        if not pixmap.isNull():
            self.background.setPixmap(pixmap)
            self.background.setScaledContents(True)
        else:
            self.background.setStyleSheet("background-color: #1a1a1a;")
        self.background.setGeometry(0, 0, 1280, 720)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Save/Load buttons

        presets_layout = QHBoxLayout()
        
        btn_style = """
            QPushButton {
                background-color: #333;
                color: #eee;
                border: 1px solid #555;
                padding: 4px 55px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #444;
                border: 1px solid #888;
            }
            QPushButton:pressed {
                background-color: #222;
            }
        """

        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet(btn_style)
        self.save_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.save_btn.clicked.connect(self.save_preset_dialog)

        self.load_btn = QPushButton("Load")
        self.load_btn.setStyleSheet(btn_style)
        self.load_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.load_btn.clicked.connect(self.load_preset_dialog)

        presets_layout.addStretch() 
        presets_layout.addWidget(self.load_btn)
        presets_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(presets_layout)

        # Spectrogram block
        vis_container = QWidget()
        vis_container.setFixedHeight(270)
        vis_layout = QVBoxLayout(vis_container)
        vis_layout.setContentsMargins(0,0,0,0)
        
        raw_spectrogram = SpectrogramWidget(engine, parent=self)
        
        self.spectrogram_frame = SpectrogramFrame(raw_spectrogram, parent=self)
        
        vis_layout.addWidget(self.spectrogram_frame)
        main_layout.addWidget(vis_container)

        # Controllers block
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        # OSC 1
        self.osc1 = OscPanel(self, "OSC 1", engine, 1, wavetables)
        controls_layout.addWidget(self.osc1)

        # OSC 2
        self.osc2 = OscPanel(self, "OSC 2", engine, 2, wavetables)
        controls_layout.addWidget(self.osc2)
        
        # OSC 3
        self.osc3 = OscPanel(self, "OSC 3", engine, 3, wavetables)
        controls_layout.addWidget(self.osc3)
        
        # Line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #444;")
        controls_layout.addWidget(line)

        # ADSR 
        self.adsr = AdsrPanel(self, "ENVELOPE", engine)
        controls_layout.addWidget(self.adsr)
        
        main_layout.addLayout(controls_layout)
        main_layout.addStretch()

        # Keys processing
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.mousePressEvent = lambda e: self.setFocus()

    # Presets
        
    def _get_presets_dir(self):
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[2]
        user_dir = project_root / "user"
        
        if not user_dir.exists():
            try:
                user_dir.mkdir(parents=True, exist_ok=True)
                print(f"[System] Created user directory: {user_dir}")
            except Exception as e:
                print(f"[Error] Could not create user dir: {e}")
                return str(project_root)
                
        return str(user_dir)
        
    def save_preset_dialog(self):
        state = {
            "osc1": self.osc1.get_state(),
            "osc2": self.osc2.get_state(),
            "osc3": self.osc3.get_state(),
            "adsr": self.adsr.get_state()
        }

        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Preset", 
            self._get_presets_dir(), 
            "JSON Files (*.json)"
        )

        if file_path:
            if not file_path.endswith(".json"):
                file_path += ".json"

            if Path(file_path).name.lower() == "default.json":
                QMessageBox.warning(
                    self, 
                    "Wrong name!", 
                    "The 'default.json' file is system.\n"
                    "Please choose other name for the preset."
                )
                return
            
            try:
                with open(file_path, 'w') as f:
                    json.dump(state, f, indent=4)
                print(f"[System] Preset saved: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save preset:\n{e}")

    def load_preset_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Load Preset", 
            self._get_presets_dir(), 
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    state = json.load(f)
                
                if "osc1" in state: self.osc1.set_state(state["osc1"])
                if "osc2" in state: self.osc2.set_state(state["osc2"])
                if "osc3" in state: self.osc3.set_state(state["osc3"])
                if "adsr" in state: self.adsr.set_state(state["adsr"])
                
                print(f"[System] Preset loaded: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load preset:\n{e}")
    
    # Key events
                
    def keyPressEvent(self, event: QKeyEvent):
        if event.isAutoRepeat(): return
        key = event.key()
        key_map = {
            Qt.Key.Key_Z: 60, Qt.Key.Key_S: 61, Qt.Key.Key_X: 62, Qt.Key.Key_D: 63,
            Qt.Key.Key_C: 64, Qt.Key.Key_V: 65, Qt.Key.Key_G: 66, Qt.Key.Key_B: 67,
            Qt.Key.Key_H: 68, Qt.Key.Key_N: 69, Qt.Key.Key_J: 70, Qt.Key.Key_M: 71
        }

        if key in key_map:
            base_note = key_map[key]
            offset = 0

            # Check shift or ctrl pressed
            modifiers = event.modifiers()
            
            # SHIFT -> Octave up (+12)
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                offset += 12
            
            # CONTROL (Ctrl) -> Octave down (-12)
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                offset -= 12
            
            final_note = base_note + offset
            
            self.active_keys[key] = final_note
            self.engine.note_on(final_note, 1.0)
            
    def keyReleaseEvent(self, event: QKeyEvent):
        if event.isAutoRepeat(): return
        
        key = event.key()
        
        if key in self.active_keys:
            note_to_off = self.active_keys[key]
            
            self.engine.note_off(note_to_off)
            
            del self.active_keys[key]