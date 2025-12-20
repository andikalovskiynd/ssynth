import sys
import os
from pathlib import Path
import sounddevice as sd
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDir
import PyQt6

# QTPlugins search and paths
dirname = os.path.dirname(PyQt6.__file__)
plugin_path = os.path.join(dirname, 'Qt6', 'plugins')
os.environ['QT_PLUGIN_PATH'] = plugin_path
print(f"[System] QT_PLUGIN_PATH set to: {plugin_path}")

current_dir = Path(__file__).resolve().parent
build_dir = current_dir / "build"

if str(build_dir) not in sys.path:
    sys.path.insert(0, str(build_dir))

try:
    import ssynth_cpp
    print("[Core] Engine module imported successfully")
except ImportError as e:
    print(f"[Fatal] Could not import ssynth_cpp: {e}")
    sys.exit(1)

# --- 

SAMPLE_RATE = 44100
BLOCK_SIZE = 512

QDir.addSearchPath("gui", str(current_dir / "frontend" ))

def main():
    engine = ssynth_cpp.Engine(SAMPLE_RATE)
    
    tables_dir = current_dir / "tables"
    wavetables = {} 
    
    required_tables = ["sine", "saw", "square", "triangle"]
    print(f"[Core] Loading wavetables from: {tables_dir}")

    for name in required_tables:
        path = tables_dir / f"{name}.wvt"
        if path.exists():
            tid = engine.load_wavetable(name, str(path))
            wavetables[name.capitalize()] = tid
            print(f"  [+] Loaded {name} -> ID {tid}")
        else:
            print(f"  [!] Missing table: {path}")

    try:
        app = QApplication(sys.argv)
    except Exception as e:
        print(f"[Fatal] Failed to init Qt Application: {e}")
        print("Tip: Try running 'pip install --force-reinstall PyQt6'")
        sys.exit(1)
    
    from frontend.gui.window_gui import MainWindow
    window = MainWindow(engine, wavetables)
    window.show()

    # Audio callback
    def audio_callback(outdata, frames, time, status):
        if status:
            print(f"[Audio Status] {status}", file=sys.stderr)
        engine.process(outdata)

    try:
        stream = sd.OutputStream(
            channels=2, 
            samplerate=SAMPLE_RATE, 
            blocksize=BLOCK_SIZE, 
            callback=audio_callback
        )
        stream.start()
        print("[System] Audio Started. Application Running...")
        
        # Start of QT Events cycle
        exit_code = app.exec()
        
        stream.stop()
        stream.close()
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"[Fatal] Audio Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()