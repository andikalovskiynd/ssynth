from PyQt6.QtWidgets import QApplication
from window_gui import MainWindow
from PyQt6.QtGui import QPixmap

import sys
import os

qt_plugins = "/Users/cyrep/Documents/python/ENTER/lib/python3.13/site-packages/PyQt6/Qt6/plugins"
os.environ["QT_PLUGIN_PATH"] = qt_plugins
print("QT_PLUGIN_PATH =", qt_plugins)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show() 
    pix = QPixmap("assets/knob/frame_0.png")
    print(pix.isNull())  
    sys.exit(app.exec())

if __name__ == "__main__":
    main()