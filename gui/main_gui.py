from PyQt6.QtWidgets import QApplication
from gui.window_gui import MainWindow
from PyQt6.QtGui import QPixmap

import sys
import os

qt_plugins = "/Users/cyrep/Documents/python/ENTER/lib/python3.13/site-packages/PyQt6/Qt6/plugins"
os.environ["QT_PLUGIN_PATH"] = qt_plugins
print("QT_PLUGIN_PATH =", qt_plugins)

def main(data=None, sample_rate=44100):
    app = QApplication(sys.argv)
    window = MainWindow(data=data, sample_rate=sample_rate)
    window.show() 
    pix = QPixmap("gui:assets/knob/frame_0.png")
    print(pix.isNull())
    sys.exit(app.exec())

if __name__ == "__main__":
    main()