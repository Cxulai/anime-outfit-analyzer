"""Anime result panel — shows annotated anime image."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap


class AnimePanel(QWidget):
    export_requested = pyqtSignal()
    ANIME_STYLES = ["赛璐珞风", "新海诚风", "吉卜力风", "漫画线稿"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_pixmap: QPixmap | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Header
        header = QLabel("动漫化结果")
        header.setStyleSheet("color: #a6adc8; font-size: 12px; padding: 2px 0; border: none;")
        layout.addWidget(header)

        # Image area
        self._label = QLabel("生成动漫图后显示在这里")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("""
            QLabel {
                border: 2px dashed #313244;
                border-radius: 12px;
                color: #585b70;
                font-size: 14px;
                background-color: #11111b;
            }
        """)
        self._label.setMinimumSize(320, 320)
        layout.addWidget(self._label, 1)

        # Spinner
        self._spinner = QLabel("生成中...")
        self._spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._spinner.setStyleSheet("color: #f9e2af; font-size: 13px; border: none; padding: 4px;")
        self._spinner.hide()
        layout.addWidget(self._spinner)

        # Export
        self._export_btn = QPushButton("导出动漫图")
        self._export_btn.clicked.connect(self.export_requested.emit)
        self._export_btn.setEnabled(False)
        self._export_btn.setStyleSheet("""
            QPushButton {
                background: #a6e3a1; color: #11111b; font-weight: bold;
                border: none; border-radius: 6px; padding: 6px 14px; font-size: 12px;
            }
            QPushButton:hover { background: #94e2d5; }
            QPushButton:disabled { background: #313244; color: #585b70; }
        """)
        layout.addWidget(self._export_btn)

    def show_loading(self):
        self._spinner.show()
        self._export_btn.setEnabled(False)

    def set_result(self, pixmap: QPixmap):
        self._current_pixmap = pixmap
        scaled = pixmap.scaled(
            self._label.width() - 20, self._label.height() - 20,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._label.setPixmap(scaled)
        self._label.setStyleSheet("""
            QLabel {
                border: 1px solid #313244; border-radius: 12px;
                background-color: #11111b;
            }
        """)
        self._spinner.hide()
        self._export_btn.setEnabled(True)

    def set_error(self, message: str):
        self._label.setText(f"生成失败\n{message}")
        self._label.setStyleSheet("""
            QLabel {
                border: 2px dashed #f38ba8; border-radius: 12px;
                color: #f38ba8; font-size: 13px;
                background-color: #11111b; padding: 24px;
            }
        """)
        self._spinner.hide()
        self._export_btn.setEnabled(False)

    def reset(self):
        self._label.setText("生成动漫图后显示在这里")
        self._label.setStyleSheet("""
            QLabel {
                border: 2px dashed #313244; border-radius: 12px;
                color: #585b70; font-size: 14px;
                background-color: #11111b;
            }
        """)
        self._spinner.hide()
        self._export_btn.setEnabled(False)
        self._current_pixmap = None

    @property
    def current_pixmap(self) -> QPixmap | None:
        return self._current_pixmap
