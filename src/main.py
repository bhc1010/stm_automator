import sys
import qdarktheme
from pathlib import Path

from PySide6 import QtCore
from PySide6.QtWidgets import QApplication

from ui.app import Ui_MainWindow

QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

app = QApplication(sys.argv)
style = Path('src/ui/style/style.css').read_text()

qdarktheme.setup_theme(
    theme="light",
    custom_colors={
            "background": "#fff",
    },
    additional_qss=style
)

win = Ui_MainWindow()
win.setStyleSheet(style)

win.show()

app.exec()