"""Anime Outfit Analyzer — entry point."""
import sys
import traceback
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow


def _excepthook(exc_type, exc_value, exc_tb):
    """Global exception handler — show error in message box."""
    tb = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(tb, file=sys.stderr, flush=True)
    QMessageBox.critical(None, "Error", f"程序崩溃:\n\n{tb[-500:]}")
    sys.exit(1)


def main():
    sys.excepthook = _excepthook

    app = QApplication(sys.argv)
    app.setApplicationName("Anime Outfit Analyzer")
    app.setStyle("Fusion")

    app.setStyleSheet("""
        QMainWindow { background-color: #11111b; }
        QWidget { background-color: #11111b; color: #cdd6f4; }
        QLabel { color: #cdd6f4; background: transparent; }
        QPushButton {
            background-color: #313244; color: #cdd6f4;
            border: none; border-radius: 6px;
            padding: 6px 16px; font-size: 13px;
        }
        QPushButton:hover { background-color: #45475a; }
        QPushButton:pressed { background-color: #585b70; }
        QPushButton:disabled { background-color: #1e1e2e; color: #585b70; }
        QComboBox {
            background-color: #1e1e2e; color: #cdd6f4;
            border: 1px solid #313244; border-radius: 6px;
            padding: 4px 8px;
        }
        QScrollArea { border: none; background: transparent; }
        QScrollBar:vertical { background: #11111b; width: 6px; }
        QScrollBar::handle:vertical { background: #45475a; border-radius: 3px; min-height: 20px; }
        QScrollBar::handle:vertical:hover { background: #585b70; }
        QSplitter::handle { background: #313244; }
        QGroupBox { color: #f9e2af; border: 1px solid #313244; border-radius: 8px; margin-top: 8px; padding-top: 16px; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
    """)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
