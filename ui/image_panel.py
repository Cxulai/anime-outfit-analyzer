"""Original image panel with drag-drop + click."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap


class ImagePanel(QWidget):
    image_loaded = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_path: str | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header = QLabel("原始图片")
        header.setStyleSheet("color: #a6adc8; font-size: 12px; padding: 2px 0; border: none;")
        layout.addWidget(header)

        self._label = QLabel("拖拽图片到此处\n或点击选择文件")
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
        self._label.mousePressEvent = self._on_click
        layout.addWidget(self._label, 1)

        self.setAcceptDrops(True)

    def _on_click(self, event):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if path:
            self.load_image(path)

    def load_image(self, path: str):
        self._file_path = path
        pix = QPixmap(path)
        if pix.isNull():
            self._label.setText("无法加载图片")
            return
        scaled = pix.scaled(
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
        self.image_loaded.emit(path)

    @property
    def file_path(self) -> str | None:
        return self._file_path

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp")):
                self.load_image(path)
